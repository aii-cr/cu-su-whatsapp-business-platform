"""Unassign tags from conversation endpoint."""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse

from app.config.error_codes import ErrorCode, get_error_response
from app.core.logger import logger
from app.services.auth import require_permissions
from app.db.models.auth import User
from app.schemas.whatsapp.chat.tag import ConversationTagUnassignRequest
from app.services import tag_service, conversation_service, audit_service
from app.core.error_handling import handle_database_error
from app.core.middleware import get_correlation_id
from bson import ObjectId

router = APIRouter()

@router.delete("/{conversation_id}/tags", status_code=status.HTTP_200_OK)
async def unassign_tags_from_conversation(
    conversation_id: str,
    unassign_data: ConversationTagUnassignRequest,
    current_user: User = Depends(require_permissions(["conversation:tags:assign"]))
):
    """
    Unassign tags from a conversation.
    
    Args:
        conversation_id: ID of the conversation
        unassign_data: Tag unassignment data
        current_user: Current authenticated user
        
    Returns:
        Success message with count of unassigned tags
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
            tag_object_ids = [ObjectId(tag_id) for tag_id in unassign_data.tag_ids]
        except Exception:
            return get_error_response(ErrorCode.INVALID_ID, "Invalid tag ID format")
        
        logger.info(
            f"🗑️ [UNASSIGN_TAGS] Unassigning {len(unassign_data.tag_ids)} tags from conversation {conversation_id}",
            extra={
                "user_id": str(current_user.id),
                "conversation_id": conversation_id,
                "tag_ids": unassign_data.tag_ids,
                "correlation_id": correlation_id
            }
        )
        
        # Check if conversation exists
        conversation = await conversation_service.get_conversation(conversation_object_id)
        if not conversation:
            return get_error_response(ErrorCode.CONVERSATION_NOT_FOUND, "Conversation not found")
        
        # Get tag details for audit logging before unassigning
        existing_tags = await tag_service.get_conversation_tags(conversation_object_id)
        tags_to_remove = [tag for tag in existing_tags if tag["tag"]["id"] in tag_object_ids]
        
        # Unassign tags using service
        unassigned_count = await tag_service.unassign_tags_from_conversation(
            conversation_id=conversation_object_id,
            tag_ids=tag_object_ids,
            unassigned_by=current_user.id
        )
        
        # ===== AUDIT LOGGING =====
        for tag_info in tags_to_remove:
            await audit_service.log_conversation_tag_removed(
                actor_id=str(current_user.id),
                actor_name=current_user.name or current_user.email,
                conversation_id=conversation_id,
                customer_phone=conversation.get("customer_phone"),
                tag_id=str(tag_info["tag"]["id"]),
                tag_name=tag_info["tag"]["name"],
                correlation_id=correlation_id
            )
        
        logger.info(
            f"✅ [UNASSIGN_TAGS] Successfully unassigned {unassigned_count} tags from conversation {conversation_id}",
            extra={
                "user_id": str(current_user.id),
                "conversation_id": conversation_id,
                "unassigned_count": unassigned_count,
                "correlation_id": correlation_id
            }
        )
        
        return JSONResponse(
            content={
                "message": f"Successfully unassigned {unassigned_count} tag(s)",
                "unassigned_count": unassigned_count
            },
            status_code=status.HTTP_200_OK
        )
        
    except ValueError as e:
        logger.warning(
            f"⚠️ [UNASSIGN_TAGS] Validation error: {str(e)}",
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
            f"❌ [UNASSIGN_TAGS] Unexpected error: {str(e)}",
            extra={
                "user_id": str(current_user.id),
                "conversation_id": conversation_id,
                "error": str(e),
                "correlation_id": correlation_id
            }
        )
        raise handle_database_error(e, "unassign_tags_from_conversation", "conversation_tag")



