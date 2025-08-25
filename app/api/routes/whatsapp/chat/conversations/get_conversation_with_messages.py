"""Get conversation with messages endpoint - Optimized for performance."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import Optional
from pydantic import BaseModel

from app.config.error_codes import ErrorCode, get_error_response
from app.core.logger import logger
from app.services.auth import require_permissions
from app.db.models.auth import User
from app.schemas.whatsapp.chat.conversation import ConversationResponse
from app.schemas.whatsapp.chat.message_out import MessageResponse
from app.services import conversation_service, audit_service
from app.core.error_handling import handle_database_error
from app.core.middleware import get_correlation_id

router = APIRouter()

class ConversationWithMessagesResponse(BaseModel):
    """Response model for conversation with messages."""
    conversation: ConversationResponse
    messages: list[MessageResponse]
    messages_total: int
    messages_limit: int
    messages_offset: int
    has_more_messages: bool
    initial_unread_count: int  # WhatsApp-like unread count for banner display

@router.get("/{conversation_id}/with-messages", response_model=ConversationWithMessagesResponse)
async def get_conversation_with_messages(
    conversation_id: str,
    messages_limit: int = Query(50, ge=1, le=100, description="Number of recent messages to return"),
    messages_offset: int = Query(0, ge=0, description="Number of messages to skip"),
    current_user: User = Depends(require_permissions(["conversations:read", "messages:read"]))
):
    """
    Get conversation details with recent messages in a single optimized call.
    
    This endpoint reduces the number of API calls and database queries by:
    1. Fetching conversation and messages in a single service call
    2. Using optimized aggregation queries
    3. Proper caching headers for performance
    4. Minimal data transfer
    
    Args:
        conversation_id: ID of the conversation
        messages_limit: Number of recent messages to return (max 100)
        messages_offset: Number of messages to skip for pagination
        current_user: Current authenticated user
        
    Returns:
        Conversation details with recent messages
    """
    correlation_id = get_correlation_id()
    
    try:
        logger.info(
            f"🚀 [GET_CONVERSATION_WITH_MESSAGES] Loading conversation {conversation_id} with {messages_limit} messages",
            extra={
                "conversation_id": conversation_id,
                "messages_limit": messages_limit,
                "messages_offset": messages_offset,
                "user_id": str(current_user.id),
                "correlation_id": correlation_id
            }
        )
        
        # Get conversation with messages using optimized service method
        result = await conversation_service.get_conversation_with_messages(
            conversation_id=conversation_id,
            user_id=current_user.id,
            is_super_admin=current_user.is_super_admin,
            messages_limit=messages_limit,
            messages_offset=messages_offset
        )
        
        if not result:
            logger.warning(
                f"❌ [GET_CONVERSATION_WITH_MESSAGES] Conversation {conversation_id} not found",
                extra={
                    "conversation_id": conversation_id,
                    "user_id": str(current_user.id),
                    "correlation_id": correlation_id
                }
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=get_error_response(ErrorCode.CONVERSATION_NOT_FOUND)
            )
        
        if not result.get("has_access"):
            logger.warning(
                f"🚫 [GET_CONVERSATION_WITH_MESSAGES] Access denied to conversation {conversation_id}",
                extra={
                    "conversation_id": conversation_id,
                    "user_id": str(current_user.id),
                    "correlation_id": correlation_id
                }
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=get_error_response(ErrorCode.CONVERSATION_ACCESS_DENIED)
            )
        
        # ===== AUDIT LOGGING =====
        await audit_service.log_conversation_accessed(
            actor_id=str(current_user.id),
            actor_name=current_user.name or current_user.email,
            conversation_id=conversation_id,
            customer_phone=result["conversation"].get("customer_phone"),
            messages_loaded=len(result["messages"]),
            correlation_id=correlation_id
        )
        
        logger.info(
            f"✅ [GET_CONVERSATION_WITH_MESSAGES] Successfully loaded conversation {conversation_id} with {len(result['messages'])} messages",
            extra={
                "conversation_id": conversation_id,
                "messages_loaded": len(result["messages"]),
                "total_messages": result["messages_total"],
                "user_id": str(current_user.id),
                "correlation_id": correlation_id
            }
        )
        
        return ConversationWithMessagesResponse(
            conversation=ConversationResponse(**result["conversation"]),
            messages=[MessageResponse(**msg) for msg in result["messages"]],
            messages_total=result["messages_total"],
            messages_limit=messages_limit,
            messages_offset=messages_offset,
            has_more_messages=result["messages_total"] > (messages_offset + len(result["messages"])),
            initial_unread_count=result["initial_unread_count"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"💥 [GET_CONVERSATION_WITH_MESSAGES] Error loading conversation {conversation_id}: {str(e)}",
            extra={
                "conversation_id": conversation_id,
                "user_id": str(current_user.id),
                "error": str(e),
                "correlation_id": correlation_id
            },
            exc_info=True
        )
        raise handle_database_error(e, "get_conversation_with_messages", "conversation")