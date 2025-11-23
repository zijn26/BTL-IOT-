from fastapi import APIRouter, HTTPException, Depends, status
from app.middleware.auth import get_current_user
from pydantic import BaseModel
from app.database import db
router = APIRouter(prefix="/dashborad", tags=["Dashborad"])

class BlockRequest(BaseModel):
    id : int 
    token_verify: str
    pin_label:str 
    device_name : str
    virtual_pin : int
    label_block : str
    type_block : int # 0 : nut , 1 : bieu do 
@router.post("/block", response_model=dict)
async def post_block(
    block_request: BlockRequest,
    current_user: dict = Depends(get_current_user)
):
    """Block user"""
    try:
        if block_request.id < 0 :
            #insert dashboard config
            result = db.execute_query(
                table="dashboard_config",
                operation="insert",
                data={
                    "user_id": current_user["id"],
                    "device_name": block_request.device_name,
                    "virtual_pin": block_request.virtual_pin,
                    "pin_label": block_request.pin_label,
                    "label_block": block_request.label_block,
                    "typeblock": block_request.type_block,
                    "token_verify": block_request.token_verify
                }
            )
            if not result:
                return {
                    "success": False,
                    "message": "Failed to set dashboard config"
                }
            return {
                "success": True,
                "message": "Dashboard config Setted successfully"
            }
        #update dashboard config
        result = db.execute_query(
            table="dashboard_config",
            operation="update",
            data={
                "device_name": block_request.device_name,
                "virtual_pin": block_request.virtual_pin,
                "pin_label": block_request.pin_label,
                "label_block": block_request.label_block,
                "typeblock": block_request.type_block,
                "token_verify": block_request.token_verify
            },
            filters={"user_id": current_user["id"], "id": block_request.id}
        )
        return {
            "success": True,
            "message": "Dashboard config Updated successfully"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to block user: {str(e)}"
        )
@router.get("/blocks", response_model=dict)
async def get_blocks(
    typeblock : int,
    current_user: dict = Depends(get_current_user)
):
    """Get blocks of user"""
    try:
        result = db.execute_query(
            table="dashboard_config",
            operation="select",
            filters={"user_id": current_user["id"], "typeblock": typeblock}
        )
        return {
            "success": True,
            "blocks": result
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get blocks: {str(e)}"
        )
@router.delete("/block", response_model=dict)
async def delete_block(
    id: int,
    current_user: dict = Depends(get_current_user)
):
    """Delete block of user"""
    try:
        result = db.execute_query(
            table="dashboard_config",
            operation="delete",
            filters={"id": id, "user_id": current_user["id"]}
        )
        return {
            "success": True,
            "message": "Block deleted successfully"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete block: {str(e)}"
        )