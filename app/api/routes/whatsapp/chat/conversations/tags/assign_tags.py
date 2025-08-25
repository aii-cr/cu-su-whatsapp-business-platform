"""Assign tags to conversation endpoint following send_message.py pattern."""

from typing import List
from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, status

from app.config.error_codes import ErrorCode
from app.core.logger import logger
from app.core.middleware import get_correlation_id
from app.db.models.auth import User
from app.schemas.whatsapp.chat.tag import TagAssign, ConversationTag, TagSummary
from app.services import audit_service, conversation_service
from app.services.auth import require_permissions
from app.services.whatsapp.tag_service import tag_service
from app.core.error_handling import handle_database_error

router = APIRouter()


@router.post("/{conversation_id}/tags", response_model=List[ConversationTag], status_code=status.HTTP_201_CREATED)
async def assign_tags_to_conversation(
    conversation_id: str,
    assign_data: TagAssign,
    current_user: User = Depends(require_permissions(["messages:send"]))
):
    """
    Assign tags to a conversation.
    
    Requires 'messages:send' permission (same as sending messages).
    """
    logger.info(f"🏷️ [ASSIGN_TAGS] Assigning {len(assign_data.tag_ids)} tags to conversation {conversation_id}")
    logger.info(f"👤 [ASSIGN_TAGS] User: {current_user.email} (ID: {current_user.id})")
    
    try:
        # Validate conversation exists
        conversation = await conversation_service.get_conversation(conversation_id)
        if not conversation:
            logger.error(f"❌ [ASSIGN_TAGS] Conversation not found: {conversation_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorCode.CONVERSATION_NOT_FOUND
            )
        
        # Convert tag IDs to ObjectId
        try:
            tag_object_ids = [ObjectId(tag_id) for tag_id in assign_data.tag_ids]
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid tag ID format"
            )
        
        # Assign tags using service
        assignments = await tag_service.assign_tags(
            ObjectId(conversation_id),
            tag_object_ids,
            current_user.id,
            auto_assigned=assign_data.auto_assigned
        )
        
        # Convert to response format matching frontend expectations
        tag_responses = []
        for assignment in assignments:
            tag_summary = TagSummary(
                id=str(assignment["tag_id"]),
                name=assignment["tag_name"],
                slug=assignment.get("tag_slug", assignment["tag_name"].lower().replace(" ", "-")),
                display_name=assignment["tag_name"],
                category=assignment.get("tag_category", "general"),
                color=assignment["tag_color"],
                usage_count=0  # Not relevant for assignments
            )
            
            tag_responses.append(ConversationTag(
                tag=tag_summary,
                assigned_at=assignment["assigned_at"].isoformat(),
                assigned_by=str(assignment["assigned_by"]) if assignment.get("assigned_by") else None,
                auto_assigned=assignment.get("auto_assigned", False)
            ))
        
        # Audit logging
        correlation_id = get_correlation_id()
        await audit_service.log_event(
            action="tags_assigned",
            actor_id=str(current_user.id),
            actor_name=current_user.name or current_user.email,
            conversation_id=conversation_id,
            payload={
                "assigned_count": len(assignments),
                "tag_ids": assign_data.tag_ids
            },
            correlation_id=correlation_id
        )
        
        logger.info(f"✅ [ASSIGN_TAGS] Successfully assigned {len(assignments)} tags")
        
        return tag_responses
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ [ASSIGN_TAGS] Unexpected error: {str(e)}")
        raise handle_database_error(e, "assign_tags", "conversation_tag")
