# Device management
# app/routers/devices.py
from unittest import result
from fastapi import APIRouter, HTTPException, Depends, status
from typing import List
import secrets
from pydantic.type_adapter import P
from app.schemas.device import DeviceRegister, DeviceResponse, DeviceConfigRequest, DeviceUpdateRequest
from app.middleware.auth import get_current_user
from app.security import create_device_token, verify_device_token
from app.database import db

router = APIRouter(prefix="/devices", tags=["Device Management"])
#đăng ký thiết bị
@router.post("/registerDevide", response_model=dict)
def register_device(
    device_data: DeviceRegister,
    current_user: dict = Depends(get_current_user)
):
    """Đăng ký ESP32 device mới"""
    try:
        # Check if device name already exists for this user
        existing_devices = db.execute_query(
            table="devices",
            operation="select",
            filters={"user_id": current_user["id"], "device_name": device_data.device_name}
        )
        
        if existing_devices:
            return{
                "success": False,
                "message": "Device name already exists"
            }
        print(f"🔍 Device data: {device_data}") 
        print(f"🔍 Current user: {current_user}") 
        # Create device in database first to get ID
        new_device = db.execute_query(
            table="devices",
            operation="insert",
            data={
                "user_id": current_user["id"],
                "device_name": device_data.device_name,
                "device_type": device_data.device_type.value,
                # "mac_address": device_data.mac_address,
                # "device_config": device_data.device_config,
                # "device_token": "temp_token"  # Temporary token
            }
        )
        
        if not new_device:
            return{
                "success": False,
                "message": "Failed to create device"
            }
        
        device = new_device[0]
        
        # Create device JWT token
        device_token = create_device_token(str(current_user["id"]),str(device["device_token"]), device_data.device_type.value)
        token_verify = secrets.token_hex(16)
        # Update device với real token
        updated_device = db.execute_query(
            table="devices",
            operation="update",
            data={"device_access_token": device_token , "token_verify" : token_verify},
            filters={"id": device["id"]}
        )
        
        # Set default permissions cho master devices
        # if device_data.device_type == "master":
        #     await db.execute_query(
        #         table="device_permissions",
        #         operation="insert",
        #         data={
        #             "device_id": device["id"],
        #             "permission_type": "ai_chat",
        #             "permission_level": "read"
        #         }
        #     )
        
        return {
            "success": True,
            "device": {
                "id": device["id"],
                "device_name": device["device_name"],
                "device_type": device["device_type"],
                # "device_access_token": device_token,
                "token_verify" : token_verify
            },
            "message": "Device registered successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Exception: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Device registration failed: {str(e)}"
        )
#lay thong tin chi tiet cua thiet bi chi dinh 
@router.get("/getDevice", response_model=dict)
async def get_device(
    device_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get device details"""
    try:
        devices = db.execute_query(
            table="devices",
            operation="select",
            filters={"user_id": current_user["id"], "id": device_id}
        )
        if not devices:
            return{
                "success": False,
                "message": "Device not found"
            }
        return {
            "success": True,
            "device": devices
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch device: {str(e)}"
        )
@router.post("/updateDevice", response_model=dict)
def update_device(
    device_data: DeviceUpdateRequest,
    current_user: dict = Depends(get_current_user)
):
    """Update device"""
    try:
        devices = db.execute_query(
            table="devices",
            operation="update",
            filters={"user_id": current_user["id"], "device_token": device_data.device_token},
            data={
                "device_name": device_data.device_name,
                "device_type": device_data.device_type.value,
                "is_active": device_data.is_active
            }
        )
        if not devices:
            return{
                "success": False,
                "message": "Device not found"
            }
        return {
            "success": True,
            "device": devices
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update device: {str(e)}"
        )
#lay danh sach thiet bi cua user
@router.get("/getDevices", response_model=dict)
async def get_devices(
    current_user: dict = Depends(get_current_user)
):
    """Get all devices of user"""
    try:
        devices = db.execute_query(
            table="devices",
            operation="select",
            filters={"user_id": current_user["id"]}
        )
        for device in devices:
            if not verify_device_token(device["device_access_token"]) :
                device["is_active"] = False
                db.execute_query(
                    table="devices",
                    operation="update",
                    data={"is_active": False},
                    filters={"id": device["id"]}
                )
        
        return {
            "success": True,
            "count": len(devices),
            "devices": devices
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch devices: {str(e)}"
        )
@router.get("/getMasterDevice", response_model=dict)
def get_master_device(
    current_user: dict = Depends(get_current_user)
):
    """Get master device of user"""
    try:
        devices = db.execute_query(
            table="devices",
            operation="select",
            filters={"user_id": current_user["id"], "device_type": "MASTER"}
        )
        return {
            "success": True,
            "devices": devices
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch master device: {str(e)}"
        )
@router.get("/getSlaveDevice", response_model=dict)
def get_slave_device(
    current_user: dict = Depends(get_current_user)
):
    """Get slave device of user"""
    try:
        devices = db.execute_query(
            table="devices",
            operation="select",
            filters={"user_id": current_user["id"], "device_type": "SLAVE"}
        )
        return {
            "success": True,
            "devices": devices
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch slave device: {str(e)}"
        )

@router.post("/configPin", response_model=dict)
def config_device(
    device_Config: DeviceConfigRequest,
    current_user: dict = Depends(get_current_user)
):
    """Confog lai thiet bi """
    try:

        devices = db.execute_query(
            table="devices",
            operation="select",
            filters={"user_id": current_user["id"], "device_token": device_Config.device_token}
        )
        
        if not devices:
            return{
                "success": False,
                "message": "Device not found"
            }
        if devices[0]["device_type"] == "MASTER":
            return{
                "success": False,
                "message": "Master device cannot be configured"
            }
        listConfigPin = db.execute_query(
            table="device_pins",
            operation="select",
            filters={"device_token": device_Config.device_token}
        )
        listConfigPin = [pin["virtual_pin"] for pin in listConfigPin]

        for pin in device_Config.pins:
            if pin.virtual_pin in listConfigPin:
                result = db.execute_query(
                    table="device_pins",
                    operation="update",
                    data={
                        "pin_label": pin.pin_label,
                        "pin_type": pin.pin_type.value,
                        "data_type": pin.data_type.value,
                        "ai_keywords": pin.ai_keywords if pin.pin_type.value == "OUTPUT" else ""
                    },
                    filters={"device_token": device_Config.device_token, "virtual_pin": pin.virtual_pin}
                )
            else:
                result = db.execute_query(
                    table="device_pins",
                    operation="insert",
                    data={
                        "device_token": device_Config.device_token,
                        "virtual_pin": pin.virtual_pin,
                        "pin_label": pin.pin_label,
                        "pin_type": pin.pin_type.value,
                        "data_type": pin.data_type.value,
                        "ai_keywords": pin.ai_keywords if pin.pin_type.value == "OUTPUT" else ""
                    }
                )
            if not result:
                return {
                    "success": False,
                    "message": "Failed to update device pins"
                }

        return {
            "success": True,
            "message": "Device Updated successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Device registration failed: {str(e)}"
        )
@router.delete("/deleteConfigPin", response_model=dict)
def delete_config_pin(
    device_token: str,
    virtual_pin: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete config pin of device"""
    try:
        result = db.execute_query(
            table="device_pins",
            operation="delete",
            filters={"device_token": device_token, "virtual_pin": int(virtual_pin)}
        )
        if not result:
            return{
                "success": False,
                "message": "Failed to delete config pin"
            }
        return {
            "success": True,
            "message": "Config pin deleted successfully"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete config pin: {str(e)}"
        )
#lay danh sach config pin cua thiet bi
@router.get("/getConfigPin", response_model=dict)
def get_config_pin(
    device_token: str,
    current_user: dict = Depends(get_current_user)
):
    """Get config pin of device"""
    try:

        devices = db.execute_query(
            table="devices",
            operation="select",
            filters={"user_id": current_user["id"], "device_token": device_token}
        )
        if not devices:
            return{
                "success": False,
                "message": "Device not found"
            }
        config_pins = db.execute_query(
            table="device_pins",
            operation="select",
            filters={"device_token": device_token}
        )
        if not config_pins:
            return{
                "success": False,
                "message": "Config pin not found"
            }
        return {
            "success": True,
            "config_pins": config_pins
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch config pin: {str(e)}"
        )
@router.delete("/deleteDevice")
def delete_device(
    device_token: str,
    current_user: dict = Depends(get_current_user)
):
    """Xóa device"""
    try:
        # Check if device belongs to user
        devices = db.execute_query(
            table="devices",
            operation="select",
            filters={"user_id": current_user["id"], "device_token": device_token}
        )
        
        if not devices:
            return{
                "success": False,
                "message": "Device not found"
            }
        
        # Delete device (cascade will handle related data)
        result = db.execute_query(
            table="devices",
            operation="delete",
            filters={"user_id": current_user["id"], "device_token": device_token}    
        )
        if not result:
            return{
                "success": False,
                "message": "Failed to delete device"
            }
        return {"success": True, "message": "Device deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete device: {str(e)}"
        )
