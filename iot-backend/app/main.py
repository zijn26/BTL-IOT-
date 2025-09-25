from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import auth, devices

app = FastAPI(
    title="IoT Backend API",
    description="API for IoT device management",
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

@app.get("/")
async def root():
    return {
        "message": "IoT Backend API is running!",
        "docs": "/docs",
        "redoc": "/redoc",
        "test_interface": "Open frontend_test.html in browser"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "message": "API is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)