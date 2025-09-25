import queue
import threading
import paho.mqtt.client as mqtt
import json
import numpy as np
import wave
import io
import asyncio
import requests
from collections import defaultdict
import librosa
import scipy.signal
from threading import Thread
import time

class MQTTAudioProcessor:
    def __init__(self):
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
    
        # Session management
        self.active_sessions = defaultdict(lambda: {
            'chunks': {},
            'metadata': {},
            'last_chunk': -1,
            'buffer': bytearray(),
            'start_time': time.time()
        })
        
        # Thêm trạng thái processing
        self.processing_sessions = queue.Queue()  # Các session đang xử lý
        self.worker_thread = threading.Thread(target=self.worker_loop)
        self.worker_thread.daemon = True
        self.wit_token = "YOUR_WIT_TOKEN"
        
    def on_connect(self, client, userdata, flags, rc):
        print(f"🌐 Connected to MQTT broker with result code {rc}")
        client.subscribe("audio/session/+")
        client.subscribe("audio/meta/+") 
        client.subscribe("audio/data/+")
        
    def on_message(self, client, userdata, msg):
        topic_parts = msg.topic.split('/')
        message_type = topic_parts[1]
        device_id = topic_parts[2]
        
        if message_type == "session":
            self.handle_session_start(device_id, msg.payload)
        elif message_type == "meta":
            self.handle_chunk_metadata(device_id, msg.payload)
        elif message_type == "data":
            self.handle_chunk_data(device_id, msg.payload)
    
    def handle_session_start(self, device_id, payload):
        session_info = json.loads(payload.decode())
        session_id = session_info['session_id']
        
        print(f"🎙️ New session started: {session_id}")
        
        # Initialize session
        self.active_sessions[session_id] = {
            'device_id': device_id,
            'chunks': {},
            'metadata': session_info,
            'last_chunk': -1,
            'buffer': bytearray(),
            'start_time': time.time()
        }
    
    def handle_chunk_metadata(self, device_id, payload):
        meta = json.loads(payload.decode())
        session_id = meta['session_id']
        chunk_id = meta['chunk_id']
        
        if session_id in self.active_sessions:
            self.active_sessions[session_id]['chunks'][chunk_id] = {
                'metadata': meta,
                'audio_data': None,
                'received_time': time.time()
            }
    
    def handle_chunk_data(self, device_id, payload):
        # Tìm chunk metadata tương ứng
        for session_id, session in self.active_sessions.items():
            if session['device_id'] == device_id:
                # Find latest chunk without audio data
                for chunk_id in sorted(session['chunks'].keys(), reverse=True):
                    if session['chunks'][chunk_id]['audio_data'] is None:
                        session['chunks'][chunk_id]['audio_data'] = payload
                        
                        print(f"📥 Received chunk {chunk_id} for session {session_id}")
                        
                        # CHỈ xử lý nếu chưa đang gửi lên Wit.ai
                        # if session_id not in self.processing_sessions:
                        #     self.process_chunk_if_ready(session_id, chunk_id)
                        # else:
                        #     print(f"⏳ Session {session_id} is processing, queuing chunk {chunk_id}")
                        # break
                        self.process_chunk_if_ready(session_id, chunk_id)
                break
    
    def process_chunk_if_ready(self, session_id, chunk_id):
        session = self.active_sessions[session_id]
        chunk = session['chunks'][chunk_id]
        
        if chunk['audio_data'] is not None:
            # Convert binary to int16 array
            audio_data = np.frombuffer(chunk['audio_data'], dtype=np.int16)
            
            print(f"🔄 Processing chunk {chunk_id}: {len(audio_data)} samples")
            
            # Advanced audio processing
            processed_audio = self.advanced_audio_processing(audio_data, session['metadata'])
            
            # Add to session buffer
            session['buffer'].extend(processed_audio.tobytes())
            session['last_chunk'] = chunk_id
            
            # Check if we have enough audio for STT (~2-3 seconds)
            buffer_duration = len(session['buffer']) / 2 / session['metadata']['sample_rate']
            
            # CHỈ gửi nếu chưa đang xử lý
            if buffer_duration >= 2.5 and session_id not in self.processing_sessions:
                self.send_to_wit_ai(session_id)
    
    def advanced_audio_processing(self, audio_data, metadata):
        """Advanced server-side audio processing"""
        # Convert to float
        audio = audio_data.astype(np.float32) / 32767.0
        
        # 1. Noise reduction using spectral subtraction
        audio = self.spectral_noise_reduction(audio, metadata['sample_rate'])
        
        # 2. Advanced AGC with multi-band processing
        audio = self.multiband_agc(audio, metadata['sample_rate'])
        
        # 3. Speech enhancement using Wiener filtering
        audio = self.wiener_filter_enhancement(audio)
        
        # 4. Dynamic range compression
        audio = self.smart_compressor(audio)
        
        # 5. Final normalization
        audio = self.normalize_for_stt(audio)
        
        return (audio * 32767).astype(np.int16)
    
    def spectral_noise_reduction(self, audio, sample_rate):
        """Advanced spectral noise reduction"""
        # Estimate noise from first 0.5 seconds
        noise_samples = int(0.5 * sample_rate)
        noise_spectrum = np.abs(np.fft.rfft(audio[:noise_samples]))
        
        # Apply spectral subtraction
        audio_fft = np.fft.rfft(audio)
        magnitude = np.abs(audio_fft)
        phase = np.angle(audio_fft)
        
        # Adaptive subtraction
        alpha = 2.0  # Over-subtraction factor
        beta = 0.01  # Floor factor
        
        gain = 1.0 - alpha * (noise_spectrum / (magnitude + 1e-10))
        gain = np.maximum(gain, beta * np.ones_like(gain))
        
        clean_magnitude = magnitude * gain
        clean_fft = clean_magnitude * np.exp(1j * phase)
        
        return np.fft.irfft(clean_fft, len(audio))
    
    def multiband_agc(self, audio, sample_rate):
        """Multi-band AGC for speech enhancement"""
        # Define frequency bands
        bands = [(80, 250), (250, 1000), (1000, 4000), (4000, 8000)]
        processed_bands = []
        
        for low_freq, high_freq in bands:
            # Bandpass filter
            nyquist = sample_rate / 2
            low = low_freq / nyquist
            high = high_freq / nyquist
            
            if high >= 1.0:
                high = 0.99
                
            b, a = scipy.signal.butter(4, [low, high], btype='band')
            band_audio = scipy.signal.filtfilt(b, a, audio)
            
            # AGC for this band
            rms = np.sqrt(np.mean(band_audio**2))
            if rms > 1e-6:
                target_rms = 0.1  # Target level
                gain = target_rms / rms
                gain = np.clip(gain, 0.1, 10.0)  # Limit gain
                band_audio *= gain
            
            processed_bands.append(band_audio)
        
        # Combine bands
        return np.sum(processed_bands, axis=0)
    
    def wiener_filter_enhancement(self, audio):
        """Wiener filter for speech enhancement"""
        # Simple Wiener filter implementation
        # This is a placeholder - you can implement more sophisticated filtering
        return audio
    
    def smart_compressor(self, audio):
        """Smart dynamic range compression"""
        # Simple compression - you can implement more sophisticated compression
        threshold = 0.3
        ratio = 4.0
        
        # Apply compression
        compressed = np.where(
            np.abs(audio) > threshold,
            np.sign(audio) * (threshold + (np.abs(audio) - threshold) / ratio),
            audio
        )
        
        return compressed
    
    def normalize_for_stt(self, audio):
        """Final normalization optimized for STT"""
        # Target peak level: -12 dBFS
        peak = np.max(np.abs(audio))
        if peak > 0:
            target_peak = 10**(-12/20)  # -12 dBFS
            gain = target_peak / peak
            audio *= gain
        
        return audio
    
    async def send_to_wit_ai(self, session_id):
        """Send accumulated buffer to Wit.ai"""
        session = self.active_sessions[session_id]
        
        if len(session['buffer']) == 0:
            return
        
        # ĐÁNH DẤU đang xử lý
        # self.processing_sessions.add(session_id)
        print(f"📤 Sending {len(session['buffer'])} bytes to Wit.ai...")
        
        # Create WAV file in memory
        wav_buffer = io.BytesIO()
        with wave.open(wav_buffer, 'wb') as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(session['metadata']['sample_rate'])
            wav_file.writeframes(session['buffer'])
        
        wav_data = wav_buffer.getvalue()
        
        # Send to Wit.ai
        headers = {
            'Authorization': f'Bearer {self.wit_token}',
            'Content-Type': 'audio/wav'
        }
        
        try:
            response = requests.post(
                'https://api.wit.ai/speech',
                headers=headers,
                data=wav_data[44:],  # Skip WAV header
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                text = result.get('text', '')
                
                print(f"🎯 Wit.ai result: {text}")
                
                # Send result back to ESP32
                self.send_result_to_device(session['device_id'], text, result)
                
                # Clear buffer for next batch
                session['buffer'] = bytearray()
                
        except Exception as e:
            print(f"❌ Wit.ai error: {e}")
            self.send_error_to_device(session['device_id'], str(e))
        
        finally:
            # BỎ ĐÁNH DẤU xử lý xong
            self.processing_sessions.discard(session_id)
            print(f"✅ Session {session_id} processing completed")
    
    def send_result_to_device(self, device_id, text, full_result):
        """Send STT result back to ESP32"""
        response = {
            'type': 'transcription',
            'text': text,
            'confidence': full_result.get('confidence', 0.0),
            'timestamp': time.time()
        }
        
        topic = f"audio/response/{device_id}"
        self.client.publish(topic, json.dumps(response))
        print(f"�� Sent result to {device_id}: {text}")
    
    def send_error_to_device(self, device_id, error_message):
        """Send error message back to ESP32"""
        response = {
            'type': 'error',
            'message': error_message,
            'timestamp': time.time()
        }
        
        topic = f"audio/response/{device_id}"
        self.client.publish(topic, json.dumps(response))
        print(f"❌ Sent error to {device_id}: {error_message}")
    
    def start(self):
        self.client.connect("your-mqtt-broker.com", 1883, 60)
        self.client.loop_forever()

if __name__ == "__main__":
    processor = MQTTAudioProcessor()
    processor.start()