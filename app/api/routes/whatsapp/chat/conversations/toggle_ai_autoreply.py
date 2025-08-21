git a"""Toggle AI auto-reply for conversations."""

from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, Field
from typing import Dict, Any

from app.schemas import SuccessResponse, ErrorResponse
from app.services.auth.utils.session_auth import get_current_user
from app.services.whatsapp.conversation import conversation_service
from app.core.logger import logger

router = APIRouter()


class ToggleAIAutoreplyRequest(BaseModel):
    """Request model for toggling AI auto-reply."""
    enabled: bool = Field(..., description="Whether to enable or disable AI auto-reply")


class ToggleAIAutoreplyResponse(BaseModel):
    """Response model for AI auto-reply toggle."""
    conversation_id: str
    ai_autoreply_enabled: bool
    updated_at: str


@router.patch("/{conversation_id}/ai-autoreply")
async def toggle_ai_autoreply(
    conversation_id: str,
    request: ToggleAIAutoreplyRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
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
    try:
        # Check if conversation exists
        conversation = await conversation_service.get_conversation(conversation_id)
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        
        # Toggle AI auto-reply
        updated_conversation = await conversation_service.toggle_ai_autoreply(
            conversation_id=conversation_id,
            enabled=request.enabled,
            updated_by=current_user.get("_id")
        )
        
        if not updated_conversation:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update AI auto-reply setting"
            )
        
        # Log the action
        action = "enabled" if request.enabled else "disabled"
        logger.info(
            f"User {current_user.get('email')} {action} AI auto-reply for "
            f"conversation {conversation_id}"
        )
        
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
        logger.error(f"Error toggling AI auto-reply for conversation {conversation_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get("/{conversation_id}/ai-autoreply/status")
async def get_ai_autoreply_status(
    conversation_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> SuccessResponse:
    """
    Get AI auto-reply status for a conversation.
    
    **Description**: Check whether AI auto-reply is enabled for a specific conversation.
    
    **Parameters**:
    - `conversation_id`: The ID of the conversation to check
    
    **Returns**: Current AI auto-reply status
    """
    try:
        # Get conversation
        conversation = await conversation_service.get_conversation(conversation_id)
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
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
        logger.error(f"Error getting AI auto-reply status for conversation {conversation_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )
