"""Get conversation endpoint."""

from fastapi import APIRouter, Depends, HTTPException, status

from app.config.error_codes import ErrorCode
from app.core.logger import logger
from app.services.auth import require_permissions
from app.db.models.auth import User
from app.schemas.whatsapp.chat.conversation_out import ConversationResponse
from app.services import conversation_service
from app.core.error_handling import handle_database_error

router = APIRouter()

@router.get("/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: str,
    current_user: User = Depends(require_permissions(["conversations:read"]))
):
    """
    Get a specific conversation by ID.
    
    Args:
        conversation_id: ID of the conversation
        current_user: Current authenticated user
        
    Returns:
        Conversation details
    """
    try:
        # Get conversation using service
        conversation = await conversation_service.get_conversation(conversation_id)
        
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorCode.CONVERSATION_NOT_FOUND
            )
        
        logger.info(f"Retrieved conversation {conversation_id} for user {current_user.id}")
        
        return ConversationResponse(**conversation)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving conversation {conversation_id}: {str(e)}")
        raise handle_database_error(e, "get_conversation", "conversation") 