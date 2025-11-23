"""
AI Chat Router - Endpoint để chat với AI và điều khiển thiết bị
Hỗ trợ multi-user với conversation history theo client_id
"""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional, Dict
from app.services.conversation_service import conversation_service
from app.services.tool_service import registry
from fastapi import Depends
from app.middleware.auth import get_current_user
from app.database import db
router = APIRouter(prefix="/ai", tags=["AI Chat"])


class ChatRequest(BaseModel):
    client_id: str
    message: str
    metadata: Optional[Dict] = None


class ChatResponse(BaseModel):
    client_id: str
    response: str
    tool_calls: List[dict]
    message_count: int
class ConfigAIRequest(BaseModel):
    token_verify: str
    name : str
    style: str
    describe: str

@router.post("/config_ai")
async def config_ai(request: ConfigAIRequest , current_user: dict = Depends(get_current_user)):
    """
    Config AI
    """
    try:
        agent_config = db.execute_query(
            table="agent_config",
            operation="select",
            filters={"token_verify": request.token_verify}
        )
        if agent_config:
            agent_config = db.execute_query(
                table="agent_config",
                operation="update",
                data={
                    "name": request.name,
                    "style": request.style,
                    "describe": request.describe
                },
                filters={"token_verify": request.token_verify}
            )
        else:
            agent_config = db.execute_query(
                table="agent_config",
                operation="insert",
                data={
                    "token_verify": request.token_verify,
                    "name": request.name,
                    "style": request.style,
                    "describe": request.describe
                }
            )
        conversation_service.clear_agent_config(request.token_verify)
        conversation_service.clear_conversation(request.token_verify)
        return agent_config
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
@router.get("/config_ai")
async def get_config_ai(token_verify: str):
    """
    Get config AI
    """
    agent_config = db.execute_query(
        table="agent_config",
        operation="select",
        filters={"token_verify": token_verify}
    )
    if agent_config:
        return agent_config
    else:
        return {
            "success": False,
            "message": "Agent config not found"
        }

@router.post("/chat")
async def chat_with_ai(request: ChatRequest):
    """
    Hoat dong ngon nghe
    VVVVVVVVVVVVVVVVVVV
    Chat với AI để điều khiển thiết bị IoT
    Hỗ trợ multi-user với conversation history tự động theo client_id
    
    Example:
    ```json
    {
        "client_id": "user_123",
        "message": "Bật đèn phòng khách",
        "metadata": {
            "user_name": "Nguyễn Văn A",
            "device_type": "mobile"
        }
    }
    ```
    
    Response:
    ```json
    {
        "client_id": "user_123",
        "response": "Đã bật đèn phòng khách thành công!",
        "tool_calls": [...],
        "message_count": 2
    }
    ```
    """
    result = await conversation_service.chat(
        client_id=request.client_id,
        user_message=request.message,
        metadata=request.metadata
    )
    
    return result


@router.get("/tools")
async def list_available_tools():
    """
    Hoat dong ngon nghe
    VVVVVVVVVVVVVVVVVVV
    Liệt kê tất cả các tools có sẵn
    """
    tools = registry.get_schemas()
    
    return tools


@router.get("/conversation/{client_id}")
async def get_conversation_history(client_id: str):
    """
    Lấy lịch sử hội thoại của một client
    
    Example:
    ```
    GET /ai/conversation/user_123
    ```
    
    Response:
    ```json
    {
        "client_id": "user_123",
        "history": [
            {"role": "user", "content": "Bật đèn"},
            {"role": "assistant", "content": "Đã bật đèn"}
        ],
        "message_count": 2,
        "metadata": {...}
    }
    ```
    """
    history = conversation_service.get_conversation_history(client_id)
    metadata = conversation_service.get_conversation_metadata(client_id)
    
    if not history:
        raise HTTPException(status_code=404, detail=f"Không tìm thấy conversation cho client {client_id}")
    
    return {
        "client_id": client_id,
        "history": history,
        "message_count": len(history),
        "metadata": metadata
    }


@router.delete("/conversation/{client_id}")
async def clear_conversation(client_id: str):
    """
    Xóa lịch sử hội thoại của một client
    
    Example:
    ```
    DELETE /ai/conversation/user_123
    ```
    """
    conversation_service.clear_conversation(client_id)
    
    return {
        "message": f"Đã xóa conversation của client {client_id}",
        "success": True
    }


@router.get("/conversations")
async def list_all_conversations():
    """
    Liệt kê tất cả các conversation đang hoạt động
    
    Response:
    ```json
    {
        "total_active_clients": 5,
        "total_messages": 24,
        "clients": {
            "user_123": {
                "message_count": 4,
                "last_activity": "2025-01-01T10:30:00",
                "metadata": {...}
            }
        }
    }
    ```
    """
    stats = conversation_service.get_statistics()
    return stats


@router.get("/conversations/clients")
async def get_active_clients():
    """
    Lấy danh sách client IDs đang có conversation
    
    Response:
    ```json
    {
        "clients": ["user_123", "device_456", "esp32_789"],
        "count": 3
    }
    ```
    """
    clients = conversation_service.get_all_active_clients()
    
    return {
        "clients": clients,
        "count": len(clients)
    }


class ExecuteToolRequest(BaseModel):
    tool_name: str
    arguments: Dict


@router.post("/execute-tool")
async def execute_tool_directly(request: ExecuteToolRequest):
    """
    Hoat dong ngon nghe
    VVVVVVVVVVVVVVVVVVV
    Thực thi một tool trực tiếp (dùng để test)
    
    Example 1 - Bật thiết bị:
    ```json
    {
        "tool_name": "turn_on_device",
        "arguments": {
            "device_name": "Đèn phòng khách"
        }
    }
    ```
    
    Example 2 - Tắt thiết bị:
    ```json
    {
        "tool_name": "turn_off_device",
        "arguments": {
            "device_name": "Quạt phòng ngủ"
        }
    }
    ```
    
    Example 3 - Điều chỉnh độ sáng:
    ```json
    {
        "tool_name": "set_brightness",
        "arguments": {
            "device_name": "Đèn phòng khách",
            "brightness": 75
        }
    }
    ```
    
    Example 4 - Liệt kê thiết bị:
    ```json
    {
        "tool_name": "list_all_devices",
        "arguments": {}
    }
    ```
    """
    # return {
    #     "tool": request.tool_name,
    #     "arguments": request.arguments,
    #     "result": "Tool executed successfully",
    #     "success": True
    # }
    result = await registry.execute(request.tool_name, request.arguments)
    
    return {
        "tool": request.tool_name,
        "arguments": request.arguments,
        "result": result,
        "success": True
    }
