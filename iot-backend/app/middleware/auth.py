# JWT verification
# app/middleware/auth.py
from fastapi import HTTPException, status, Request, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.security import verify_token, verify_device_token
from app.database import db

security = HTTPBearer()

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Middleware để get current user từ JWT token"""
    try:
        print(f"🔍 Token: {credentials}")  # Debug token
        payload = verify_token(credentials.credentials)
        if payload is None:
            raise HTTPException( 
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials cai token này"
            )
        
        # Get user from database
        print(f"🔍 Looking for user_id: {payload['user_id']}")  # Debug user_id
        users = db.execute_query(
            table="users",
            operation="select", 
            filters={"id": payload["user_id"]}
        )
        print(f"🔍 Users found: {users}")  # Debug users
        
        if not users:
            print("❌ No users found in database")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        
        user = users[0]
        print(f"🔍 User: {user}")  # Debug user
        
        if not user.get("is_active", False):
            print("❌ User is inactive")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Inactive user"
            )
        
        print("✅ User authenticated successfully")
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Exception: {e}")  # Debug exception
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials" + str(e)
        )
def get_current_device(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Middleware để get current ESP32 device từ device token"""
    try:
        payload = verify_device_token(credentials.credentials)
        if payload is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid device token"
            )
        
        # Get device from database
        devices =  db.execute_query(
            table="devices",
            operation="select",
            filters={"id": payload["user_id"]}  # device_id stored in "sub"
        )
        if not devices:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Device not found"
            )
        return devices[0]
        
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid device token"
        )
