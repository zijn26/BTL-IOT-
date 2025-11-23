# User authentication
# app/routers/auth.py
from fastapi import APIRouter, HTTPException, Depends, status
from datetime import timedelta
from app.schemas.auth import UserRegister, UserLogin, Token, UserResponse
from app.security import verify_password, get_password_hash, create_access_token
from app.database import db
from app.config import settings
from app.middleware.auth import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=Token)
def register_user(user_data: UserRegister):
    """Đăng ký user mới
    Args: type 0 : admin , 1 : observer
    """
    try:
        # Check if user already exists
        existing_users = db.execute_query(
            table="users",
            operation="select",
            filters={"email": user_data.email}
        )
        
        if existing_users:
            return {
                "success": False,
                "message": "Email already registered"
            }
        
        # Hash password
        hashed_password = get_password_hash(user_data.password)
        
        # Create user
        new_user = db.execute_query(
            table="users",
            operation="insert",
            data={
                "email": user_data.email,
                "name": user_data.name,
                "password_hash": hashed_password,
                "type": user_data.type
            }
        )
        
        if not new_user:
            return {
                "success": False,
                "message": "Failed to create user"
            }
        
        user = new_user[0]
        
        # Create access token
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": str(user["id"])}, 
            expires_delta=access_token_expires
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user["id"],
                "email": user["email"],
                "name": user["name"],
                "is_active": user["is_active"],
                "type": user["type"]
            }
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": f"Registration failed: {str(e)}"
        }

@router.post("/login", response_model=Token)
def login_user(user_data: UserLogin):
    """Đăng nhập user"""
    try:
        # Find user by email
        users = db.execute_query(
            table="users",
            operation="select",
            filters={"email": user_data.email}
        )
        
        if not users:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        user = users[0]
        
        # Verify password
        if not verify_password(user_data.password, user["password_hash"]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        if not user["is_active"]:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Account is inactive"
            )
        
        # Create access token
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": str(user["id"])},
            expires_delta=access_token_expires
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user["id"],
                "email": user["email"],
                "name": user["name"],
                "is_active": user["is_active"],
                "type": user["type"]
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed: {str(e)}"
        )

@router.get("/me", response_model=UserResponse)
def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """Get thông tin user hiện tại"""
    return UserResponse(
        id=current_user["id"],
        email=current_user["email"],
        name=current_user["name"],
        is_active=current_user["is_active"],
        created_at=str(current_user["created_at"]),
        type=current_user["type"]
    )

