from fastapi import APIRouter, HTTPException, Depends, WebSocketDisconnect, status
from app.middleware.auth import get_current_device, get_current_user
from pydantic import BaseModel
from app.database import db
from fastapi import WebSocket
from concurrent.futures import ThreadPoolExecutor
from app.services.STTSystem import STTSystem
from app.services.mqtt_service import mqtt_service
from app.services.conversation_service import conversation_service
import asyncio

router = APIRouter(prefix="/audio_stream", tags=["Audio Stream"])
TAG = "AUDIO_STREAM"
class AudioStreamRequest(BaseModel):
    id : int 
    token_verify: str
    pin_label:str 
    device_name : str
    virtual_pin : int
executor_stt = ThreadPoolExecutor(max_workers=4, thread_name_prefix="STTSystem-Worker")

@router.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """
    WebSocket endpoint để nhận audio stream từ ESP32 và xử lý STT
    """
    await websocket.accept()
    print(f"{TAG} CONNECTION: Client {client_id} đã kết nối.")
    
    # Khởi tạo STT system cho client này
    stt_system = STTSystem(max_workers=1, token_master=client_id)
    chunk_count = 0
    
    try:
        while True:
            # Kiểm tra trạng thái voice từ MQTT
            if client_id in mqtt_service.client_is_voice and mqtt_service.client_is_voice[client_id]:
                # Client đang gửi audio
                data = await websocket.receive_bytes()
                chunk_count += 1
                
                # ✅ FIX: Xử lý audio chunk ĐÚNG CÁCH
                # Sử dụng asyncio.to_thread() để chạy sync function trong thread pool
                await asyncio.to_thread(stt_system.process_chunk, data)
                
                if chunk_count % 10 == 0:
                    print(f"{TAG} Client {client_id}: Đã nhận {chunk_count} chunks")
            else:
                # Client ngừng gửi audio, lấy kết quả STT
                print(f"{TAG} Client {client_id}: Kết thúc ghi âm, đang lấy kết quả...")
                
                text = stt_system.get_result_text()
                
                if not text or text.strip() == "":
                    text = "Không nhận diện được giọng nói"
                
                print(f"{TAG} STT Result: {text}")
                
                # Gửi kết quả về client
                await websocket.send_text(text)
                await websocket.close()
                result = await conversation_service.chat(client_id, text)
                print(f"{TAG} [Client: {client_id}] Result: {result}")
                return
                
    except WebSocketDisconnect:
        print(f"{TAG} CONNECTION: Client {client_id} đã ngắt kết nối.")
        
        # Lấy kết quả cuối cùng nếu có
        final_transcript = stt_system.get_result_text()
        if final_transcript:
            print(f"{TAG} FINAL TRANSCRIPT: {final_transcript}")
    
    except Exception as e:
        print(f"{TAG} ERROR: Lỗi với client {client_id}: {e}")
        import traceback
        traceback.print_exc()
        
        try:
            await websocket.close()
        except:
            pass