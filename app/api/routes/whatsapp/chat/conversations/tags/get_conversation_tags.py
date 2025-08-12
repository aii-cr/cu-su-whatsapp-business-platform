"""Get conversation tags endpoint."""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from typing import List

from app.config.error_codes import ErrorCode, get_error_response
from app.core.logger import logger
from app.services.auth import require_permissions
from app.db.models.auth import User
from app.schemas.whatsapp.chat.tag import ConversationTagResponse
from app.services import tag_service, conversation_service
from app.core.error_handling import handle_database_error
from app.core.middleware import get_correlation_id
from bson import ObjectId

router = APIRouter()

@router.get("/{conversation_id}/tags", response_model=List[ConversationTagResponse])
async def get_conversation_tags(
    conversation_id: str,
    current_user: User = Depends(require_permissions(["conversations:read"]))
):
    """
    Get all tags assigned to a conversation.
    
    Args:
        conversation_id: ID of the conversation
        current_user: Current authenticated user
        
    Returns:
        List of conversation tag assignments
    """
    correlation_id = get_correlation_id()
    
    try:
        # Validate conversation_id
        try:
            conversation_object_id = ObjectId(conversation_id)
        except Exception:
            return get_error_response(ErrorCode.INVALID_ID, "Invalid conversation ID format")
        
        logger.info(
            f"🔍 [GET_CONVERSATION_TAGS] Getting tags for conversation {conversation_id}",
            extra={
                "user_id": str(current_user.id),
                "conversation_id": conversation_id,
                "correlation_id": correlation_id
            }
        )
        
        # Check if conversation exists
        conversation = await conversation_service.get_conversation(conversation_object_id)
        if not conversation:
            return get_error_response(ErrorCode.CONVERSATION_NOT_FOUND, "Conversation not found")
        
        # Get conversation tags using service
        conversation_tags = await tag_service.get_conversation_tags(conversation_object_id)
        
        # Convert to response format
        tag_responses = []
        for conv_tag in conversation_tags:
            tag_response = ConversationTagResponse(
                conversation_id=str(conv_tag["conversation_id"]),
                tag=conv_tag["tag"],
                assigned_at=conv_tag["assigned_at"],
                assigned_by=str(conv_tag["assigned_by"]) if conv_tag.get("assigned_by") else None,
                auto_assigned=conv_tag.get("auto_assigned", False),
                confidence_score=conv_tag.get("confidence_score")
            )
            tag_responses.append(tag_response)
        
        logger.info(
            f"✅ [GET_CONVERSATION_TAGS] Found {len(tag_responses)} tags for conversation {conversation_id}",
            extra={
                "user_id": str(current_user.id),
                "conversation_id": conversation_id,
                "tags_count": len(tag_responses),
                "correlation_id": correlation_id
            }
        )
        
        return tag_responses
        
    except HTTPException:
        raise
        
    except Exception as e:
        logger.error(
            f"❌ [GET_CONVERSATION_TAGS] Unexpected error: {str(e)}",
            extra={
                "user_id": str(current_user.id),
                "conversation_id": conversation_id,
                "error": str(e),
                "correlation_id": correlation_id
            }
        )
        raise handle_database_error(e, "get_conversation_tags", "conversation_tag")
