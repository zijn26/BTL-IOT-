from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import auth, devices, mqtt, websocket , sensors , dashborad, ai_chat
from app.websockets import audio_stream
from app.services.mqtt_service import mqtt_service

# Import tools để tự động đăng ký vào registry
import app.tools

app = FastAPI(
    title="IoT Backend API",
    description="API for IoT device management with MQTT integration",
    version="1.0.0"
)

# CORS middleware để frontend có thể gọi API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Trong production nên chỉ định domain cụ thể
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(devices.router)
app.include_router(mqtt.router)
app.include_router(websocket.router)
app.include_router(sensors.router)
app.include_router(dashborad.router)
app.include_router(audio_stream.router)
app.include_router(ai_chat.router)
@app.get("/")
async def root():
    return {
        "message": "IoT Backend API is running!",
        "docs": "/docs",
        "redoc": "/redoc",
        "test_interface": "Open frontend_test.html in browser",
        "mqtt_status": mqtt_service.running,
        "mqtt_endpoints": {
            "status": "/mqtt/status",
            "start": "/mqtt/start",
            "stop": "/mqtt/stop",
            "publish": "/mqtt/publish",
            "topics": "/mqtt/topics"
        },
        "websocket_endpoints": {
            "mqtt_bridge": "/ws/mqtt",
            "test_page": "/ws/mqtt/test",
            "audio_stream": "/audio_stream/ws/{client_id}"
        }
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy", 
        "message": "API is running",
        "mqtt_broker": "running" if mqtt_service.running else "stopped"
    }

@app.on_event("startup")
async def startup_event():
    """Khởi động MQTT Broker khi FastAPI start"""
    print("🚀 Starting IoT Backend with MQTT integration...")
    # Không tự động start MQTT broker, để user control qua API
    print("💡 Use /mqtt/start endpoint to start MQTT Broker")

@app.on_event("shutdown")
async def shutdown_event():
    """Dừng MQTT Broker khi FastAPI shutdown"""
    print("🛑 Shutting down IoT Backend...")
    mqtt_service.stop_broker()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)