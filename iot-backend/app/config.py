# Settings
# app/core/config.py
import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    # Supabase
    SUPABASE_URL: str = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
    SUPABASE_ANON_KEY: str = os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY") 
    SUPABASE_SERVICE_KEY: str = os.getenv("SUPABASE_SERVICE_KEY")
    
    # JWT
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES") # 7 days
    
    # AI Services
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY")
    ACCESS_TOKEN_DEVICE_MINUTES : int = os.getenv("ACCESS_TOKEN_DEVICE_MINUTES") # 9 thang 
    # App Settings
    DEBUG: bool = os.getenv("DEBUG")
    PORT: int = os.getenv("PORT")
    
    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
