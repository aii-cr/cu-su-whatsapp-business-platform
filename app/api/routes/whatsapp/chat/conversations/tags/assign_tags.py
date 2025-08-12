"""Assign tags to conversation endpoint."""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from typing import List

from app.config.error_codes import ErrorCode, get_error_response
from app.core.logger import logger
from app.services.auth import require_permissions
from app.db.models.auth import User
from app.schemas.whatsapp.chat.tag import ConversationTagAssignRequest, ConversationTagResponse
from app.services import tag_service, conversation_service, audit_service
from app.core.error_handling import handle_database_error
from app.core.middleware import get_correlation_id
from bson import ObjectId

router = APIRouter()

@router.post("/{conversation_id}/tags", response_model=List[ConversationTagResponse], status_code=status.HTTP_201_CREATED)
async def assign_tags_to_conversation(
    conversation_id: str,
    assign_data: ConversationTagAssignRequest,
    current_user: User = Depends(require_permissions(["conversation:tags:assign"]))
):
    """
    Assign tags to a conversation.
    
    Args:
        conversation_id: ID of the conversation
        assign_data: Tag assignment data
        current_user: Current authenticated user
        
    Returns:
        List of assigned conversation tag details
    """
    correlation_id = get_correlation_id()
    
    try:
        # Validate conversation_id
        try:
            conversation_object_id = ObjectId(conversation_id)
        except Exception:
            return get_error_response(ErrorCode.INVALID_ID, "Invalid conversation ID format")
        
        # Validate tag_ids
        try:
            tag_object_ids = [ObjectId(tag_id) for tag_id in assign_data.tag_ids]
        except Exception:
            return get_error_response(ErrorCode.INVALID_ID, "Invalid tag ID format")
        
        logger.info(
            f"🏷️ [ASSIGN_TAGS] Assigning {len(assign_data.tag_ids)} tags to conversation {conversation_id}",
            extra={
                "user_id": str(current_user.id),
                "conversation_id": conversation_id,
                "tag_ids": assign_data.tag_ids,
                "auto_assigned": assign_data.auto_assigned,
                "correlation_id": correlation_id
            }
        )
        
        # Check if conversation exists
        conversation = await conversation_service.get_conversation(conversation_object_id)
        if not conversation:
            return get_error_response(ErrorCode.CONVERSATION_NOT_FOUND, "Conversation not found")
        
        # Assign tags using service
        conversation_tags = await tag_service.assign_tags_to_conversation(
            conversation_id=conversation_object_id,
            tag_ids=tag_object_ids,
            assigned_by=current_user.id,
            auto_assigned=assign_data.auto_assigned,
            confidence_scores=assign_data.confidence_scores
        )
        
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
        
        # ===== AUDIT LOGGING =====
        for conv_tag in conversation_tags:
            await audit_service.log_conversation_tag_added(
                actor_id=str(current_user.id),
                actor_name=current_user.name or current_user.email,
                conversation_id=conversation_id,
                customer_phone=conversation.get("customer_phone"),
                tag_id=str(conv_tag["tag"]["id"]),
                tag_name=conv_tag["tag"]["name"],
                auto_assigned=conv_tag.get("auto_assigned", False),
                confidence_score=conv_tag.get("confidence_score"),
                correlation_id=correlation_id
            )
        
        logger.info(
            f"✅ [ASSIGN_TAGS] Successfully assigned {len(tag_responses)} tags to conversation {conversation_id}",
            extra={
                "user_id": str(current_user.id),
                "conversation_id": conversation_id,
                "assigned_count": len(tag_responses),
                "correlation_id": correlation_id
            }
        )
        
        return tag_responses
        
    except ValueError as e:
        logger.warning(
            f"⚠️ [ASSIGN_TAGS] Validation error: {str(e)}",
            extra={
                "user_id": str(current_user.id),
                "conversation_id": conversation_id,
                "error": str(e),
                "correlation_id": correlation_id
            }
        )
        return get_error_response(ErrorCode.VALIDATION_ERROR, str(e))
        
    except HTTPException:
        raise
        
    except Exception as e:
        logger.error(
            f"❌ [ASSIGN_TAGS] Unexpected error: {str(e)}",
            extra={
                "user_id": str(current_user.id),
                "conversation_id": conversation_id,
                "error": str(e),
                "correlation_id": correlation_id
            }
        )
        raise handle_database_error(e, "assign_tags_to_conversation", "conversation_tag")



