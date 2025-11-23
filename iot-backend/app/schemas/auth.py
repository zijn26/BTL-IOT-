# Auth schemas
# app/schemas/auth.py
from pydantic import BaseModel, EmailStr
from typing import Optional

class UserRegister(BaseModel):
    email: EmailStr
    name: str
    password: str
    type : int # 0 : admin , 1 : observer

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    user: dict

class UserResponse(BaseModel):
    id: int
    email: str
    name: str
    is_active: bool
    created_at: str
    type : int # 0 : admin , 1 : observer

# app/schemas/device.py
