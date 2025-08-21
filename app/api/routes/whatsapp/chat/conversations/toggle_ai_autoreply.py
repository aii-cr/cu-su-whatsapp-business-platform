from fastapi import APIRouter, HTTPException, status, Depends, Response
from pydantic import BaseModel, Field
from typing import Dict, Any

from app.schemas import SuccessResponse, ErrorResponse
from app.services.auth import require_permissions, check_user_permission
from app.db.models.auth import User
from app.services.whatsapp.conversation import conversation_service
from app.core.logger import logger
from app.core.middleware import get_correlation_id

router = APIRouter()


class ToggleAIAutoreplyRequest(BaseModel):
    """Request model for toggling AI auto-reply."""
    enabled: bool = Field(..., description="Whether to enable or disable AI auto-reply")


class ToggleAIAutoreplyResponse(BaseModel):
    """Response model for AI auto-reply toggle."""
    conversation_id: str
    ai_autoreply_enabled: bool
    updated_at: str


@router.options("/{conversation_id}/ai-autoreply")
async def options_ai_autoreply(conversation_id: str):
    """Handle OPTIONS request for CORS preflight."""
    logger.info(f"🔧 [CORS] OPTIONS request received for conversation {conversation_id}")
    return {"message": "OK"}

@router.patch("/{conversation_id}/ai-autoreply")
async def toggle_ai_autoreply(
    conversation_id: str,
    request: ToggleAIAutoreplyRequest,
    current_user: User = Depends(require_permissions(["conversations:update"])),
    response: Response = None
) -> SuccessResponse:
    """
    Toggle AI auto-reply for a conversation.
    
    **Description**: Enable or disable automatic AI responses for a specific conversation.
    
    **Parameters**:
    - `conversation_id`: The ID of the conversation to update
    - `enabled`: Whether to enable (true) or disable (false) AI auto-reply
    
    **Returns**: Updated conversation with new AI auto-reply status
    
    **Permissions**: User must have access to the conversation
    """
    correlation_id = get_correlation_id()
    
    try:
        logger.info(
            f"🚀 [TOGGLE_AI_AUTOREPLY] Toggling AI auto-reply for conversation {conversation_id}",
            extra={
                "conversation_id": conversation_id,
                "enabled": request.enabled,
                "user_id": str(current_user.id),
                "correlation_id": correlation_id
            }
        )
        # Check if conversation exists
        conversation = await conversation_service.get_conversation(conversation_id)
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        
        # Check access permissions
        if not current_user.is_super_admin:
            if (conversation.get("assigned_agent_id") != current_user.id and 
                not await check_user_permission(current_user.id, "conversations:update_all")):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied to this conversation"
                )
        
        # Toggle AI auto-reply
        updated_conversation = await conversation_service.toggle_ai_autoreply(
            conversation_id=conversation_id,
            enabled=request.enabled,
            updated_by=current_user.id
        )
        
        if not updated_conversation:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update AI auto-reply setting"
            )
        
        # Log the action
        action = "enabled" if request.enabled else "disabled"
        logger.info(
            f"✅ [TOGGLE_AI_AUTOREPLY] User {current_user.email} {action} AI auto-reply for conversation {conversation_id}",
            extra={
                "conversation_id": conversation_id,
                "enabled": request.enabled,
                "user_id": str(current_user.id),
                "correlation_id": correlation_id
            }
        )
        
        # Send WebSocket notification about the toggle
        try:
            from app.services import websocket_service
            await websocket_service.notify_autoreply_toggled(
                conversation_id=conversation_id,
                enabled=request.enabled,
                changed_by=current_user.email
            )
            logger.info(f"🔔 [WS] Sent auto-reply toggle notification for conversation {conversation_id}")
        except Exception as ws_error:
            logger.warning(f"⚠️ [WS] Failed to send auto-reply toggle notification: {str(ws_error)}")
            # Don't fail the entire flow if WebSocket notification fails
        
        # Prepare response
        response_data = ToggleAIAutoreplyResponse(
            conversation_id=str(updated_conversation["_id"]),
            ai_autoreply_enabled=updated_conversation["ai_autoreply_enabled"],
            updated_at=updated_conversation["updated_at"].isoformat()
        )
        
        return SuccessResponse(
            message=f"AI auto-reply {action} successfully",
            data=response_data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"❌ [TOGGLE_AI_AUTOREPLY] Error toggling AI auto-reply for conversation {conversation_id}: {str(e)}",
            extra={
                "conversation_id": conversation_id,
                "user_id": str(current_user.id),
                "correlation_id": correlation_id,
                "error": str(e)
            }
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.options("/{conversation_id}/ai-autoreply/status")
async def options_ai_autoreply_status(conversation_id: str):
    """Handle OPTIONS request for CORS preflight."""
    logger.info(f"🔧 [CORS] OPTIONS status request received for conversation {conversation_id}")
    return {"message": "OK"}

@router.get("/{conversation_id}/ai-autoreply/status")
async def get_ai_autoreply_status(
    conversation_id: str,
    current_user: User = Depends(require_permissions(["conversations:read"]))
) -> SuccessResponse:
    """
    Get AI auto-reply status for a conversation.
    
    **Description**: Check whether AI auto-reply is enabled for a specific conversation.
    
    **Parameters**:
    - `conversation_id`: The ID of the conversation to check
    
    **Returns**: Current AI auto-reply status
    """
    correlation_id = get_correlation_id()
    
    try:
        logger.info(
            f"🚀 [GET_AI_AUTOREPLY_STATUS] Getting AI auto-reply status for conversation {conversation_id}",
            extra={
                "conversation_id": conversation_id,
                "user_id": str(current_user.id),
                "correlation_id": correlation_id
            }
        )
        # Get conversation
        conversation = await conversation_service.get_conversation(conversation_id)
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        
        # Check access permissions
        if not current_user.is_super_admin:
            if (conversation.get("assigned_agent_id") != current_user.id and 
                not await check_user_permission(current_user.id, "conversations:read_all")):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied to this conversation"
                )
        
        # Return AI auto-reply status
        return SuccessResponse(
            message="AI auto-reply status retrieved successfully",
            data={
                "conversation_id": str(conversation["_id"]),
                "ai_autoreply_enabled": conversation.get("ai_autoreply_enabled", True),
                "updated_at": conversation.get("updated_at", conversation["created_at"]).isoformat()
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"❌ [GET_AI_AUTOREPLY_STATUS] Error getting AI auto-reply status for conversation {conversation_id}: {str(e)}",
            extra={
                "conversation_id": conversation_id,
                "user_id": str(current_user.id),
                "correlation_id": correlation_id,
                "error": str(e)
            }
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )
