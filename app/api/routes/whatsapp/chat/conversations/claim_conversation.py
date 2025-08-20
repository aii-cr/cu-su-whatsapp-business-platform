"""
Claim conversation endpoint.
Allows agents to claim unassigned conversations.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from bson import ObjectId

from app.services.auth import require_permissions
from app.db.models.auth import User
from app.core.logger import logger
from app.core.middleware import get_correlation_id
from app.db.models.auth import User
from app.schemas.whatsapp.chat.conversation import ConversationResponse
from app.services import conversation_service
from app.services.websocket.websocket_service import manager, websocket_service
from app.config.error_codes import get_error_response, ErrorCode
from app.core.error_handling import handle_database_error

router = APIRouter()


@router.post("/{conversation_id}/claim", response_model=ConversationResponse)
async def claim_conversation(
    conversation_id: str,
    current_user: User = Depends(require_permissions(["conversations:claim"]))
):
    """
    Claim an unassigned conversation by the current agent.
    
    This endpoint allows agents to manually claim conversations that haven't been assigned yet.
    The conversation will be assigned to the current user and its status will be set to active.
    
    Args:
        conversation_id: ID of the conversation to claim
        current_user: Current authenticated user (agent)
        
    Returns:
        Updated conversation with assignment information
        
    Raises:
        404: Conversation not found
        400: Conversation already assigned or cannot be claimed
        403: User doesn't have permission to claim conversations
    """
    try:
        correlation_id = get_correlation_id()
        
        logger.info(f"🏷️ [CLAIM_CONVERSATION] Agent {current_user.email} attempting to claim conversation {conversation_id}")
        
        # Claim the conversation
        updated_conversation = await conversation_service.claim_conversation(
            conversation_id=conversation_id,
            agent_id=str(current_user.id),
            actor_id=str(current_user.id),
            correlation_id=correlation_id
        )
        
        if not updated_conversation:
            logger.warning(f"❌ [CLAIM_CONVERSATION] Failed to claim conversation {conversation_id} by agent {current_user.email}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=get_error_response(ErrorCode.CONVERSATION_ALREADY_ASSIGNED)
            )
        
        # Broadcast assignment update to all dashboard subscribers
        agent_name = current_user.name or current_user.email
        await manager.broadcast_conversation_assignment_update(
            conversation_id=conversation_id,
            assigned_agent_id=str(current_user.id),
            agent_name=agent_name
        )
        
        # Handle unread count updates for assignment change
        await websocket_service.handle_conversation_assignment_change(
            conversation_id=conversation_id,
            new_assigned_agent_id=str(current_user.id)
        )
        
        logger.info(f"✅ [CLAIM_CONVERSATION] Conversation {conversation_id} successfully claimed by agent {current_user.email}")
        
        return ConversationResponse(**updated_conversation)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ [CLAIM_CONVERSATION] Unexpected error claiming conversation {conversation_id}: {str(e)}")
        raise handle_database_error(e, "claim_conversation", "conversation")
