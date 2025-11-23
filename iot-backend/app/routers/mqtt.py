# MQTT API endpoints
# app/routers/mqtt.py
from email import message
import json
from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.responses import JSONResponse
from typing import List, Dict, Optional, Self
from pydantic import BaseModel
from app.middleware.auth import get_current_user
from app.services.mqtt_service import mqtt_service
from app.broker_server import TOPIC_CONTRO , TOPIC_SENSOR
from app.database import db
router = APIRouter(prefix="/mqtt", tags=["MQTT Management"])
TAG = "MQTT ROUTER"
# Pydantic models
class MQTTMessage(BaseModel):
    topic: str
    message: str

class MQTTSubscribe(BaseModel):
    topic: str
class MqttClientModel(BaseModel):
    token_verify: str
class MQTTPublish(BaseModel):
    topic: str
    message: str

class MQTTStatus(BaseModel):
    running: bool
    topics: List[str]
    subscribers_count: Dict[str, int]
class MqttSensorPost(BaseModel):
    virtual_pin: int
    value: str
class MqttDeviceCommand(BaseModel):
    token_verify: str
    virtual_pin: int
    value: float
@router.get("/status", response_model=MQTTStatus)
def get_mqtt_status():
    """Lấy trạng thái MQTT Broker"""
    try:
        topics = mqtt_service.get_all_topics()
        subscribers_count = {}
        
        for topic in topics:
            subscribers_count[topic] = mqtt_service.get_subscribers_count(topic)
            
        return MQTTStatus(
            running=mqtt_service.running,
            topics=topics,
            subscribers_count=subscribers_count
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get MQTT status: {str(e)}"
        )

@router.post("/start")
def start_mqtt_broker():
    """Khởi động MQTT Broker"""
    try:
        if mqtt_service.running:
            return {"message": "MQTT Broker đã đang chạy"}
            
        mqtt_service.start_broker(host= "0.0.0.0" , port= 1883)

        return {"message": "MQTT Broker đã khởi động thành công"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start MQTT Broker: {str(e)}"
        )
@router.post("/startTestClient")
def startTestClient(token_verify : MqttClientModel ):
    """Khởi động MQTT Client Test for HTTP api"""
    try :
        broker_host="localhost"
        broker_port= 1883
        if mqtt_service.client_running :
            return {"mes" : "dang chayj client roi "}

        mqtt_service.start_client(broker_host ,broker_port,  token_verify.token_verify.strip())

        if not mqtt_service.client_running:
            return {"message " : TAG + f"Khong the ket noi toi broker sever:  {broker_host} - {broker_port} - {token_verify}"}
        return {"message" : "ket noi thanh cong "}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start MQTT Client: {str(e)}"
        )

@router.post("/stop")
def stop_mqtt_broker():
    """Dừng MQTT Broker"""
    try:
        mqtt_service.stop_broker()
        return {"message": "MQTT Broker đã dừng"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to stop MQTT Broker: {str(e)}"
        )


@router.post("/stopClient")
def stop_mqtt_broker():
    """Dừng MQTT Client"""
    try:
        mqtt_service.stop_client()
        return {"message": "MQTT client đã dừng"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to stop MQTT client: {str(e)}"
        )


@router.post("/publish") # loiiiiiiiiiiiiiiii nham giua mqtt host va client
def client_publish_message(
    message_data: MQTTPublish,
    current_user: dict = Depends(get_current_user)
):
    """Publish message qua MQTT"""
    try:
        if not mqtt_service.running:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="MQTT Broker chưa khởi động"
            )
        if not mqtt_service.client_running:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="MQTT client chưa khởi động"
            )
        success = mqtt_service.mqtt_client.publish(
            message_data.topic, 
            message_data.message
        )
        
        if success:
            return {"message": "Message đã được publish thành công"}
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to publish message"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to publish message: {str(e)}"
        )

@router.get("/topics")
def get_topics():
    """Lấy danh sách tất cả topics"""
    try:
        topics = mqtt_service.get_all_topics()
        return {"topics": topics, "count": len(topics)}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get topics: {str(e)}"
        )
# deeeeeeeeee sauuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuu
@router.get("/topics/{topic}/subscribers")
def get_topic_subscribers(topic: str):
    """Lấy số lượng subscribers cho topic"""
    try:
        count = mqtt_service.get_subscribers_count(topic)
        return {"topic": topic, "subscribers_count": count}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get subscribers: {str(e)}"
        )

@router.post("/sensor-data")
def client_send_sensor_data(
    sensor_data_post: MqttSensorPost,
    # current_user: dict = Depends(get_current_user)
):
    """Gửi sensor data qua MQTT (simulate từ ESP32)"""
    try:
        if not mqtt_service.running:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="MQTT Broker chưa khởi động"
            )
        if not (mqtt_service.client_running):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="MQTT client chưa khởi động"
            )
        # Tạo topic cho sensor data
        topic = TOPIC_SENSOR  + f"{mqtt_service.mqtt_client.client_id}/{sensor_data_post.virtual_pin}"
        res  = mqtt_service.mqtt_client.publish(topic , sensor_data_post.value)
        
        
        return {
                "message": res ,
                "topic": topic,
                "value": sensor_data_post.value
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send sensor data: {str(e)}"
        )

@router.post("/device-command")
def send_device_command(
    device_command: MqttDeviceCommand,
    current_user: dict = Depends(get_current_user)
):
    """Gửi command đến device qua MQTT"""
    try:
        if not mqtt_service.running:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="MQTT Broker chưa khởi động"
            )
        device_pin = db.execute_query(
            table="device_pins",
            operation="select",
            filters={"device_token": mqtt_service.device_tokens[device_command.token_verify]["device_token"], "virtual_pin": device_command.virtual_pin}
        )
        if not device_pin:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Device pin không tồn tại"
            )
        if not device_pin[0]["pin_type"] == "OUTPUT":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Device pin không phải là OUTPUT"
            )
      
        # Tạo topic cho device command
        # topic = TOPIC_CONTRO + f"{device_token}/command"
        # message = command if not value else f"{command}:{value}"
        
        success = mqtt_service.publish_message_CT(device_command.token_verify , device_command.virtual_pin, str(device_command.value))
        
        if success:
            return {
                "message": "Device command đã được gửi thành công",
                "topic": TOPIC_CONTRO + device_command.token_verify + "/" + str(device_command.virtual_pin),
                "message": str(device_command.value)
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to send device command"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send device command: {str(e)}"
        )

# @router.get("/sensor-data")
# def get_sensor_data(
#     token_verify: str,
#     limit: int = 10,
#     virtual_pin : int = 0,
#     current_user: dict = Depends(get_current_user)
# ):
#     """Lấy sensor data từ database"""
#     try:
        
#         # Lấy sensor data từ database
#         sensor_data = db.execute_query(
#             table="sensor_data",
#             operation="select",
#             filters={"token_verify": token_verify , "virtual_pin" : virtual_pin}
#         )
        
#         if not sensor_data:
#             return {"message": "Không có sensor data", "data": []}
            
#         # Limit results
#         if(limit > 0 and limit < len(sensor_data)):
#             sensor_data = sensor_data[:limit]

#         # limit 0 thi lay het
#         return {
#             "message": "Sensor data retrieved successfully",
#             "data": sensor_data,
#             "count": len(sensor_data)
#         }
#     except Exception as e:
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=f"Failed to get sensor data: {str(e)}"
#         )
