"""Create conversation endpoint."""

from fastapi import APIRouter, Depends, HTTPException, status

from app.config.error_codes import ErrorCode
from app.core.logger import logger
from app.services.auth import require_permissions
from app.db.models.auth import User
from app.schemas.whatsapp.chat.conversation_in import ConversationCreate
from app.schemas.whatsapp.chat.conversation_out import ConversationResponse
from app.services import conversation_service
from app.core.error_handling import handle_database_error

router = APIRouter()

@router.post("/", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
async def create_conversation(
    conversation_data: ConversationCreate,
    current_user: User = Depends(require_permissions(["conversations:create"]))
):
    """
    Create a new conversation.
    
    Args:
        conversation_data: Conversation data
        current_user: Current authenticated user
        
    Returns:
        Created conversation details
    """
    try:
        # Create conversation using service
        conversation = await conversation_service.create_conversation(
            customer_phone=conversation_data.customer_phone,
            customer_name=conversation_data.customer_name,
            department_id=conversation_data.department_id,
            assigned_agent_id=conversation_data.assigned_agent_id,
            created_by=current_user.id,
            priority=conversation_data.priority,
            channel=conversation_data.channel,
            customer_type=conversation_data.customer_type,
            tags=conversation_data.tags,
            metadata=conversation_data.metadata
        )
        
        logger.info(f"Created conversation {conversation['_id']} for user {current_user.id}")
        
        return ConversationResponse(**conversation)
        
    except Exception as e:
        logger.error(f"Error creating conversation: {str(e)}")
        raise handle_database_error(e, "create_conversation", "conversation")
