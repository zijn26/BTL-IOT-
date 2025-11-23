# app/core/security.py
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from app.config import settings
from app.database import db  # ✅ Import instance db, không phải module
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> Optional[dict]:
    payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM] , subject=None)
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM] , subject=None)
        user_id = payload.get("sub")
        print(f"🔍 User ID: {user_id}")
        if user_id is None:
            return None
        user_id_int = (user_id)
        return {"user_id": user_id_int}
    except JWTError as e:
        print(f"❌ JWTError: {e}")
        return None
    except Exception as e:
        print(f"❌ Exception: {e}")
        return None

def verify_device(token: str) -> Optional[dict]:

    payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM] , subject=None)
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM] , subject=None)
        user_id = payload.get("sub")
        print(f"🔍 User ID: {user_id}")
        if user_id is None:
            return None
        user_id_int = (user_id)
        return {
            "user_id": int(payload.get("user_id")),
            "device_token": str(payload.get("sub")),
            "device_type": payload.get("device_type"),
            "type": payload.get("type")
        }
    except JWTError as e:
        print(f"❌ JWTError: {e}")
        return None
    except Exception as e:
        print(f"❌ Exception: {e}")
        return None
def create_device_token(user_id: str, device_id: str, device_type: str) -> str:
    """Create JWT token for ESP32 devices"""
    data = {
        "sub": device_id,
        "user_id": user_id,
        "device_type": device_type,
        "type": "device_token"
    }
    return create_access_token(data , timedelta(minutes=settings.ACCESS_TOKEN_DEVICE_MINUTES))

def verify_device_token(token: str) -> Optional[dict]:
    """Verify ESP32 device token"""
    payload = verify_device(token)
    if payload and payload.get("type") == "device_token":
        return {
            "user_id": int(payload.get("user_id")),
            "device_id": str(payload.get("sub")),
            "device_type": payload.get("device_type")
        }
    return None
