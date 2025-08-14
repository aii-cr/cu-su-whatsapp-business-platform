"""Unassign tags from conversation endpoint following send_message.py pattern."""

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, status

from app.config.error_codes import ErrorCode
from app.core.logger import logger
from app.core.middleware import get_correlation_id
from app.db.models.auth import User
from app.schemas.whatsapp.chat.tag import TagUnassign, TagUnassignResponse
from app.services import audit_service, conversation_service
from app.services.auth import require_permissions
from app.services.whatsapp.tag_service import tag_service
from app.core.error_handling import handle_database_error

router = APIRouter()


@router.delete("/{conversation_id}/tags", response_model=TagUnassignResponse)
async def unassign_tags_from_conversation(
    conversation_id: str,
    unassign_data: TagUnassign,
    current_user: User = Depends(require_permissions(["messages:send"]))
):
    """
    Unassign tags from a conversation.
    
    Requires 'messages:send' permission (same as sending messages).
    """
    logger.info(f"🏷️ [UNASSIGN_TAGS] Unassigning {len(unassign_data.tag_ids)} tags from conversation {conversation_id}")
    logger.info(f"👤 [UNASSIGN_TAGS] User: {current_user.email} (ID: {current_user.id})")
    
    try:
        # Validate conversation exists
        conversation = await conversation_service.get_conversation(conversation_id)
        if not conversation:
            logger.error(f"❌ [UNASSIGN_TAGS] Conversation not found: {conversation_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorCode.CONVERSATION_NOT_FOUND
            )
        
        # Convert tag IDs to ObjectId
        try:
            tag_object_ids = [ObjectId(tag_id) for tag_id in unassign_data.tag_ids]
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid tag ID format"
            )
        
        # Unassign tags using service
        unassigned_count = await tag_service.unassign_tags(
            ObjectId(conversation_id),
            tag_object_ids
        )
        
        # Audit logging
        correlation_id = get_correlation_id()
        await audit_service.log_event(
            action="tags_unassigned",
            actor_id=str(current_user.id),
            actor_name=current_user.name or current_user.email,
            details=f"Unassigned {unassigned_count} tags from conversation {conversation_id}",
            correlation_id=correlation_id
        )
        
        logger.info(f"✅ [UNASSIGN_TAGS] Successfully unassigned {unassigned_count} tags")
        
        # Return response matching frontend expectations
        message = f"Unassigned {unassigned_count} tag" + ("s" if unassigned_count != 1 else "")
        return TagUnassignResponse(
            message=message,
            unassigned_count=unassigned_count
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ [UNASSIGN_TAGS] Unexpected error: {str(e)}")
        raise handle_database_error(e, "unassign_tags", "conversation_tag")
