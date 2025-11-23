import os
import json
import queue
import threading
import time
import struct
import tempfile
from typing import Optional, List, Tuple
from collections import deque
from concurrent.futures import ThreadPoolExecutor
import numpy as np
from groq import Groq
from silero_vad import load_silero_vad, get_speech_timestamps, VADIterator
import io
from scipy import signal
import torch

class STTSystem: 
    def __init__(self, 
                 chunk_duration_seconds_max: float = 4.8,
                 chunk_duration_seconds_min: float = 1.28,
                 sample_rate: int = 16000,
                 frame_duration_ms: int = 32,
                 groq_api_key: Optional[str] = None,
                 language: str = "vi",
                 max_workers: int = 3,
                 token_master : str = None
               ):
        """
        Khởi tạo STTSystem
        
        Args:
            chunk_duration_seconds_max: Thời gian tích lũy chunk tối đa trước khi xử lý (giây)
            chunk_duration_seconds_min: Thời gian tích lũy chunk tối thiểu trước khi xử lý (giây)
            sample_rate: Tần số lấy mẫu audio (Hz)
            frame_duration_ms: Độ dài frame cho VAD (ms)
            groq_api_key: API key cho Groq (nếu None sẽ dùng biến môi trường)
            language: Ngôn ngữ cho transcription
            max_workers: Số lượng worker threads tối đa cho xử lý song song
        """
        self.chunk_duration_seconds_max = chunk_duration_seconds_max
        self.chunk_duration_seconds_min = chunk_duration_seconds_min
        self.sample_rate = sample_rate
        self.frame_duration_ms = frame_duration_ms
        self.language = language
        
        # Khởi tạo Groq client
        api_key = groq_api_key or os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("Groq API key is required. Set GROQ_API_KEY environment variable or pass groq_api_key parameter.")
        self.groq_client = Groq(api_key=api_key)
        
        # Khởi tạo Silero VAD
        print("Đang tải Silero VAD model...")
        self.vad_model = load_silero_vad(onnx=True)
        self.frame_size = int(sample_rate * frame_duration_ms / 1000)
        self.vad_threshold = 0.5
        self.vad_iterator = VADIterator(
            self.vad_model,
            threshold=self.vad_threshold,
            sampling_rate=self.sample_rate,
            min_silence_duration_ms=250,
            speech_pad_ms=30,
        )

        self.is_speaking = False

        # Hàng đợi chunk và overhead
        self.chunk_queue = deque()
        self.overhead_queue = deque()
        self.chunk_queue_duration = 0.0
        
        # Hàng đợi text với số thứ tự
        self.text_queue = queue.PriorityQueue()
        self.text_sequence = 0
        
        # Lock cho thread-safe operations
        self.lock = threading.Lock()
        
        # Thread pool executor để xử lý song song
        self.executor = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="STT-Worker")
        
        # Thread để xử lý audio chunks
        self.processing_thread = None
        self.is_running = False
        
        # Pre-compute WAV header template để tăng tốc
        self.samples_200ms = int(self.sample_rate * 0.2)
        
        # Cache cho filter coefficients
        nyquist = self.sample_rate / 2
        low_cutoff = 80 / nyquist
        self.filter_b, self.filter_a = signal.butter(3, low_cutoff, btype='high')
    
    def _normalize_audio(self, audio_data: np.ndarray) -> np.ndarray:
        """
        Chuẩn hóa âm lượng audio
        
        Args:
            audio_data: Mảng numpy chứa audio data
            
        Returns:
            Audio data đã được chuẩn hóa
        """
        if len(audio_data) == 0:
            return audio_data
        
        # Normalize về range [-1, 1]
        max_val = np.max(np.abs(audio_data))
        if max_val > 0:
            audio_data = audio_data / max_val
        
        return audio_data
    
    def _filter_noise(self, audio_data: np.ndarray) -> np.ndarray:
        """
        Lọc nhiễu từ audio sử dụng high-pass filter với cached coefficients
        
        Args:
            audio_data: Mảng numpy chứa audio data
            
        Returns:
            Audio data đã được lọc nhiễu
        """
        if len(audio_data) < 3:
            return audio_data
        
        # Sử dụng cached filter coefficients để tăng tốc
        filtered_audio = signal.filtfilt(self.filter_b, self.filter_a, audio_data)
        
        return filtered_audio

    def reset_vad_state(self):
        """
        Đặt lại trạng thái của VADIterator.
        Nên được gọi khi bắt đầu một phiên ghi âm mới.
        """
        self.vad_iterator.reset_states()
        self.is_speaking = False
        with self.lock:
            self.chunk_queue.clear()
            self.overhead_queue.clear()
            self.chunk_queue_duration = 0.0
        print("Đã reset trạng thái VAD.")

    def _detect_voice(self, audio_data: np.ndarray) -> bool:
        """
        Kiểm tra có giọng nói trong audio chunk không sử dụng Silero VAD
        Mỗi chunk được xử lý độc lập, không phụ thuộc vào các chunk khác
        
        Args:
            audio_data: Mảng numpy chứa audio data (float32 trong range [-1, 1])
            
        Returns:
            True nếu phát hiện giọng nói, False nếu không
        """
        if len(audio_data) == 0:
            return False
        
        try:
            # Đảm bảo audio_data là float32
            if audio_data.dtype != np.float32:
                audio_data = audio_data.astype(np.float32)
            
            # Chuyển đổi sang torch tensor và đảm bảo là float32
            audio_tensor = torch.from_numpy(audio_data).float()
            vad_window_size = 512 if self.sample_rate == 16000 else 256
            
            if len(audio_tensor) < vad_window_size:
                padding_size = vad_window_size - len(audio_tensor)
                audio_tensor = torch.nn.functional.pad(audio_tensor, (0, padding_size))
            elif len(audio_tensor) > vad_window_size:
                audio_tensor = audio_tensor[:vad_window_size]
            speech_dict = self.vad_iterator(audio_tensor, return_seconds=True)
            
            if speech_dict :
                return True
            else:
                return False
            
        except Exception as e:
            print(f"Error in Silero VAD detection: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _process_audio_chunk(self, audio_data: np.ndarray) -> np.ndarray:
        """
        Xử lý audio chunk: lọc nhiễu và chuẩn hóa
        
        Args:
            audio_data: Mảng numpy chứa audio data
            
        Returns:
            Audio data đã được xử lý
        """
        # Lọc nhiễu
        filtered = self._filter_noise(audio_data)
        
        # Chuẩn hóa âm lượng
        normalized = self._normalize_audio(filtered)
        
        return normalized
    
    def _merge_audio_chunks(self, chunks: List[np.ndarray]) -> np.ndarray:
        """
        Ghép các audio chunks thành một mảng duy nhất
        
        Args:
            chunks: Danh sách các audio chunks
            
        Returns:
            Audio data đã được ghép
        """
        if not chunks:
            return np.array([], dtype=np.float32)
        
        return np.concatenate(chunks)
    
    def _create_wav_in_memory(self, audio_data: np.ndarray) -> Optional[io.BytesIO]:
        """
        Tạo file WAV trong memory từ audio data - OPTIMIZED VERSION
        Sử dụng struct.pack để tạo WAV header nhanh hơn wave module
        
        Args:
            audio_data: Mảng numpy chứa audio data (float32, range [-1, 1])
            
        Returns:
            BytesIO object chứa WAV data hoặc None nếu lỗi
        """
        try:
            # Chuyển đổi sang int16 nhanh chóng
            if audio_data.dtype != np.float32:
                max_abs = np.max(np.abs(audio_data))
                if max_abs > 1.0:
                    audio_data = audio_data / max_abs
                audio_data = audio_data.astype(np.float32)
            
            # Chuyển đổi sang int16 với clip để tránh overflow
            audio_int16 = np.clip(audio_data * 32767, -32768, 32767).astype(np.int16)
            
            # Tạo WAV header bằng struct.pack (nhanh hơn wave module)
            num_samples = len(audio_int16)
            num_channels = 1
            sample_width = 2  # 16-bit = 2 bytes
            byte_rate = self.sample_rate * num_channels * sample_width
            block_align = num_channels * sample_width
            data_size = num_samples * sample_width
            
            # WAV file format header
            wav_buffer = io.BytesIO()
            
            # RIFF header
            wav_buffer.write(b'RIFF')
            wav_buffer.write(struct.pack('<I', 36 + data_size))  # File size - 8
            wav_buffer.write(b'WAVE')
            
            # fmt chunk
            wav_buffer.write(b'fmt ')
            wav_buffer.write(struct.pack('<I', 16))  # fmt chunk size
            wav_buffer.write(struct.pack('<H', 1))   # Audio format (1 = PCM)
            wav_buffer.write(struct.pack('<H', num_channels))
            wav_buffer.write(struct.pack('<I', self.sample_rate))
            wav_buffer.write(struct.pack('<I', byte_rate))
            wav_buffer.write(struct.pack('<H', block_align))
            wav_buffer.write(struct.pack('<H', 16))  # Bits per sample
            
            # data chunk
            wav_buffer.write(b'data')
            wav_buffer.write(struct.pack('<I', data_size))
            wav_buffer.write(audio_int16.tobytes())
            
            # Reset position để đọc
            wav_buffer.seek(0)
            return wav_buffer
            
        except Exception as e:
            print(f"Error creating WAV in memory: {e}")
            return None
    
    def _get_last_200ms(self, audio_data: np.ndarray) -> np.ndarray:
        """
        Lấy 200ms cuối của audio data - OPTIMIZED
        Sử dụng pre-computed samples_200ms
        
        Args:
            audio_data: Mảng numpy chứa audio data
            
        Returns:
            200ms cuối của audio data
        """
        if len(audio_data) >= self.samples_200ms:
            return audio_data[-self.samples_200ms:]
        return audio_data
    
    def _clean_text(self, text: str) -> str:
        """
        Lọc bỏ các chuỗi spam/không mong muốn từ kết quả transcription
        
        Args:
            text: Text cần lọc
            
        Returns:
            Text đã được làm sạch
        """
        if not text:
            return text
        
        # Danh sách các chuỗi spam cần loại bỏ (có thể mở rộng thêm)
        spam_phrases = [
            "Hãy subscribe cho kênh Ghiền Mì Gõ Để không bỏ lỡ những video hấp dẫn",
            "Cảm ơn các bạn đã theo dõi và hẹn gặp lại",
            "Đừng quên like và subscribe",
            "Nhấn nút subscribe để ủng hộ kênh",
            "Cảm ơn đã xem video",
            "Hẹn gặp lại trong video tiếp theo",
            "Hãy subscribe cho kênh La La School Để không bỏ lỡ những video hấp dẫn",
        ]
        
        # Loại bỏ các chuỗi spam (case-insensitive)
        cleaned_text = text
        for phrase in spam_phrases:
            # Loại bỏ cả chính xác và các biến thể viết hoa/thường
            cleaned_text = cleaned_text.replace(phrase, "")
            cleaned_text = cleaned_text.replace(phrase.lower(), "")
            cleaned_text = cleaned_text.replace(phrase.upper(), "")
        
        # Loại bỏ khoảng trắng thừa
        cleaned_text = " ".join(cleaned_text.split())
        
        return cleaned_text.strip()
    
    def process_chunk(self, chunk_data, chunk_sample_rate: Optional[int] = None) -> bool:
        """
        Method 1: Xử lý chunk data âm thanh từ websocket
        
        Nhận vào chunk data (bytes hoặc numpy array), xử lý (lọc nhiễu, chuẩn hóa, kiểm tra VAD),
        nếu có giọng nói thì thêm vào hàng đợi. Khi hàng đợi chunk tích lũy
        đủ thời gian, ghép với overhead queue và gọi method 2.
        
        Args:
            chunk_data: Dữ liệu audio chunk từ websocket (bytes hoặc numpy array)
            chunk_sample_rate: Sample rate của chunk data (nếu None sẽ dùng self.sample_rate)
            
        Returns:
            True nếu xử lý thành công, False nếu không
        """
        try:
            # Chuyển đổi chunk_data thành numpy array
            if isinstance(chunk_data, bytes):
                # Nếu là bytes, giả sử là PCM 16-bit mono
                audio_data = np.frombuffer(chunk_data, dtype=np.int16).astype(np.float32) / 32767.0
            elif isinstance(chunk_data, np.ndarray):
                audio_data = chunk_data.copy()
            else:
                print(f"Unsupported chunk data type: {type(chunk_data)}")
                return False
            
            # Kiểm tra nếu audio_data rỗng
            if len(audio_data) == 0:
                print("Empty chunk data")
                return False
            
            # Xác định sample rate
            sr = chunk_sample_rate if chunk_sample_rate is not None else self.sample_rate
            
            # Resample nếu cần
            if sr != self.sample_rate:
                num_samples = int(len(audio_data) * self.sample_rate / sr)
                audio_data = signal.resample(audio_data, num_samples)
            
            # Chuyển đổi sang mono nếu là stereo
            if len(audio_data.shape) > 1:
                audio_data = np.mean(audio_data, axis=1)
            
            # Xử lý audio (lọc nhiễu, chuẩn hóa)
            processed_audio = self._process_audio_chunk(audio_data)
            
            # Kiểm tra VAD (Silero VAD nhận float32 trực tiếp)
            # has_voice = self._detect_voice(processed_audio)
            
            # if not has_voice:
            #     # print("No voice detected in chunk")
            #     return False

            # Đảm bảo processed_audio là float32
            if processed_audio.dtype != np.float32:
                processed_audio = processed_audio.astype(np.float32)
            
            # Chuyển đổi sang torch tensor và đảm bảo là float32
            audio_tensor = torch.from_numpy(processed_audio).float()
            
            # Gọi VADIterator để cập nhật trạng thái
            speech_dict = self.vad_iterator(audio_tensor, return_seconds=True)
            if speech_dict:
                if 'start' in speech_dict:
                    self.is_speaking = True
                    print(f"Phát hiện bắt đầu nói tại: {speech_dict['start']}s")
                elif 'end' in speech_dict:
                    self.is_speaking = False
                    print(f"Phát hiện kết thúc nói tại: {speech_dict['end']}s")
            # Thêm vào hàng đợi chunk
            if self.is_speaking:
                chunk_duration = len(processed_audio) / self.sample_rate
            else :
                chunk_duration = 0.0
                return False
            
            with self.lock:
                self.chunk_queue.append(processed_audio)
                self.chunk_queue_duration += chunk_duration
                
                # Kiểm tra nếu đã tích lũy đủ thời gian
                if self.chunk_queue_duration >= self.chunk_duration_seconds_max or (self.chunk_queue_duration >= self.chunk_duration_seconds_min and self.is_speaking == False):
                    # Lấy 200ms cuối của chunk queue cho overhead
                    all_chunks = list(self.chunk_queue)
                    merged_chunks = self._merge_audio_chunks(all_chunks)
                    last_200ms = self._get_last_200ms(merged_chunks)
                    
                    # Ghép overhead queue và chunk queue
                    overhead_audio = self._merge_audio_chunks(list(self.overhead_queue))
                    chunk_audio = self._merge_audio_chunks(all_chunks)
                    final_audio = np.concatenate([overhead_audio, chunk_audio])
                    
                    # Tạo file WAV trong memory
                    wav_buffer = self._create_wav_in_memory(final_audio)
                    if wav_buffer is not None:
                        # Sử dụng thread pool executor thay vì tạo thread mới mỗi lần
                        self.executor.submit(self.transcribe_audio, wav_buffer)
                    
                    # Reset chunk queue, giữ lại overhead (200ms cuối)
                    self.chunk_queue.clear()
                    self.chunk_queue_duration = 0.0
                    # Overhead queue sẽ được cập nhật ở lần tiếp theo
                    self.overhead_queue.clear()
                    self.overhead_queue.append(last_200ms)
            
            return True
            
        except Exception as e:
            print(f"Error processing chunk: {e}")
            return False
    
    def transcribe_audio(self, wav_buffer: io.BytesIO) -> Optional[str]:
        """
        Method 2: Chuyển đổi file WAV thành text sử dụng Groq API - OPTIMIZED VERSION
        
        Sử dụng tempfile nhưng tối ưu hóa việc ghi file (write một lần thay vì nhiều lần).
        WAV creation đã được tối ưu với struct.pack ở _create_wav_in_memory.
        
        Args:
            wav_buffer: BytesIO object chứa WAV data
            
        Returns:
            Text đã được transcribe hoặc None nếu lỗi
        """
        temp_file_path = None
        try:
            if wav_buffer is None:
                print("WAV buffer is None")
                return None
            
            # Đảm bảo buffer ở vị trí đầu
            #Data giọng nói tiếng việt cho chũ hết được thêm vào cuối wav_buffer
            wav_buffer.seek(0)
            
            # Tạo file tạm và ghi toàn bộ buffer một lần (nhanh hơn nhiều lần ghi nhỏ)
            with tempfile.NamedTemporaryFile(mode='wb', suffix='.wav', delete=False) as temp_file:
                temp_file_path = temp_file.name
                # Ghi toàn bộ buffer trong một lần gọi
                temp_file.write(wav_buffer.getvalue())
                temp_file.flush()
                os.fsync(temp_file.fileno())  # Đảm bảo dữ liệu được ghi xuống disk
            
            # Gọi Groq API với file tạm
            with open(temp_file_path, 'rb') as wav_file:
                transcription = self.groq_client.audio.transcriptions.create(
                    file=wav_file,
                    model="whisper-large-v3-turbo",
                    prompt="",  # Có thể thêm context nếu cần
                    response_format="verbose_json",
                    timestamp_granularities=["word", "segment"],
                    language=self.language,
                    temperature=0.0
                )
            
            # Lấy text từ transcription
            text = transcription.text if hasattr(transcription, 'text') else str(transcription)
            
            # Lưu vào hàng đợi với số thứ tự
            with self.lock:
                sequence = self.text_sequence
                self.text_sequence += 1
                self.text_queue.put((sequence, text))
            
            print(f"Text đã được transcribe: {text}")
            return text
                
        except Exception as e:
            print(f"Error transcribing audio: {e}")
            import traceback
            traceback.print_exc()
            return None
        finally:
            # Xóa file tạm ngay lập tức để giải phóng disk space
            if temp_file_path and os.path.exists(temp_file_path):
                try:
                    os.unlink(temp_file_path)
                except Exception as e:
                    print(f"Warning: Could not delete temp file {temp_file_path}: {e}")
            
            # Đóng buffer để giải phóng memory
            if wav_buffer is not None:
                try:
                    wav_buffer.close()
                except:
                    pass
    
    def get_result_text(self) -> str:
        """
        Method 3: Ghép toàn bộ các đoạn text lại thành một đoạn text duy nhất
        
        Lấy tất cả text từ hàng đợi, sắp xếp theo số thứ tự và ghép lại.
        
        Returns:
            Đoạn text đã được ghép
        """
        if(self.chunk_queue_duration >= 0.25):
            overhead_audio = self._merge_audio_chunks(list(self.overhead_queue))
            chunk_audio = self._merge_audio_chunks(list(self.chunk_queue))
            final_audio = np.concatenate([overhead_audio, chunk_audio])
            wav_buffer = self._create_wav_in_memory(final_audio)
            self.transcribe_audio(wav_buffer)
            self.chunk_queue.clear()
            self.chunk_queue_duration = 0.0
            self.overhead_queue.clear()
        else :
            self.text_queue.put((self.text_sequence, ""))
        texts = []
            # Lấy tất cả text từ queue
        while not self.text_queue.empty():
            try:
                sequence, text = self.text_queue.get_nowait()
                texts.append((sequence, text))
            except queue.Empty:
                break
        
        # Sắp xếp theo số thứ tự
        texts.sort(key=lambda x: x[0])
        
        # Ghép lại thành một đoạn text
        combined_text = " ".join([text for _, text in texts])
        
        # Lọc bỏ các chuỗi spam/không mong muốn
        cleaned_text = self._clean_text(combined_text)
        
        self.reset_vad_state()
        return cleaned_text + "[HẾT]"
    def get_new_text(self) ->str :
        """
        Lấy kết quả mới nhất từ hàng đợi text
        """
        with self.lock:
            if not self.text_queue.empty():
                sequence, text = self.text_queue.get_nowait()
                self.text_queue.put((sequence, text))
                return text
            else:
                return None
    def clear_text_queue(self):
        """
        Xóa toàn bộ hàng đợi text
        """
        with self.lock:
            while not self.text_queue.empty():
                try:
                    self.text_queue.get_nowait()
                except queue.Empty:
                    break
            self.text_sequence = 0
    
    def get_queue_status(self) -> dict:
        """
        Lấy trạng thái của các hàng đợi
        
        Returns:
            Dictionary chứa thông tin về các hàng đợi
        """
        with self.lock:
            return {
                "chunk_queue_size": len(self.chunk_queue),
                "chunk_queue_duration": self.chunk_queue_duration,
                "overhead_queue_size": len(self.overhead_queue),
                "text_queue_size": self.text_queue.qsize(),
                "text_sequence": self.text_sequence,
                "is_speaking": self.is_speaking
            }
    
    def shutdown(self):
        """
        Tắt STTSystem và giải phóng tài nguyên
        Đóng thread pool executor để dọn dẹp threads
        """
        print("Đang shutdown STTSystem...")
        self.is_running = False
        
        # Shutdown executor và chờ các task đang chạy hoàn thành
        self.executor.shutdown(wait=True, cancel_futures=False)
        
        # Clear các queues
        with self.lock:
            self.chunk_queue.clear()
            self.overhead_queue.clear()
            while not self.text_queue.empty():
                try:
                    self.text_queue.get_nowait()
                except queue.Empty:
                    break
        
        print("STTSystem đã shutdown hoàn tất.")
    
    def __del__(self):
        """
        Destructor để đảm bảo cleanup khi object bị xóa
        """
        try:
            if hasattr(self, 'executor'):
                self.executor.shutdown(wait=False, cancel_futures=True)
        except:
            pass

