"""Delete conversation endpoint."""

from fastapi import APIRouter, Depends, HTTPException, status

from app.config.error_codes import ErrorCode
from app.core.logger import logger
from app.services.auth import require_permissions, check_user_permission
from app.db.models.auth import User
from app.schemas.whatsapp.chat.conversation_out import ConversationResponse
from app.services import conversation_service, message_service
from app.core.error_handling import handle_database_error

router = APIRouter()

@router.delete("/{conversation_id}", response_model=ConversationResponse)
async def delete_conversation(
    conversation_id: str,
    current_user: User = Depends(require_permissions(["conversations:delete"]))
):
    """
    Delete a conversation and all its messages.
    
    Args:
        conversation_id: ID of the conversation to delete
        current_user: Current authenticated user
        
    Returns:
        Deleted conversation details
    """
    try:
        # Get conversation to verify access
        conversation = await conversation_service.get_conversation(conversation_id)
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorCode.CONVERSATION_NOT_FOUND
            )
        
        # Check permissions
        if not current_user.is_super_admin:
            if (conversation.get("assigned_agent_id") != current_user.id and 
                not await check_user_permission(current_user.id, "conversations:delete_all")):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=ErrorCode.PERMISSION_DENIED
                )
        
        # Delete conversation using service
        deleted_conversation = await conversation_service.delete_conversation(conversation_id)
        
        if not deleted_conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorCode.CONVERSATION_NOT_FOUND
            )
        
        logger.info(f"Deleted conversation {conversation_id} by user {current_user.id}")
        
        return ConversationResponse(**deleted_conversation)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting conversation {conversation_id}: {str(e)}")
        raise handle_database_error(e, "delete_conversation", "conversation") 