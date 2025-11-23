from email import message
import json
from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.responses import JSONResponse
from typing import List, Dict, Optional, Self
from app.middleware.auth import get_current_user
from app.database import db

router = APIRouter(prefix="/sensors", tags=["Sensor Management"])


@router.get("/sensor-data")
def get_sensor_data(
    token_verify: str,
    limit: int = 10,
    virtual_pin : int = 0,
    current_user: dict = Depends(get_current_user)
):
    """Lấy sensor data từ database"""
    try:
        
        # Lấy sensor data từ database
        sensor_data = db.execute_query(
            table="sensor_data",
            operation="select",
            filters={"token_verify": token_verify , "virtual_pin" : virtual_pin}
        )
        
        if not sensor_data:
            return {"message": "Không có sensor data", "data": []}
            
        # Limit results
        if(limit > 0 and limit < len(sensor_data)):
            sensor_data = sensor_data[-limit:]

        # limit 0 thi lay het
        return {
            "message": "Sensor data retrieved successfully",
            "data": sensor_data,
            "count": len(sensor_data)
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get sensor data: {str(e)}"
        )
