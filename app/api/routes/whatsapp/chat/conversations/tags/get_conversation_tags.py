"""Get conversation tags endpoint following send_message.py pattern."""

from typing import List
from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, status

from app.config.error_codes import ErrorCode
from app.core.logger import logger
from app.db.models.auth import User
from app.schemas.whatsapp.chat.tag import ConversationTag, TagSummary
from app.services import conversation_service
from app.services.auth import require_permissions
from app.services.whatsapp.tag_service import tag_service
from app.core.error_handling import handle_database_error

router = APIRouter()


@router.get("/{conversation_id}/tags", response_model=List[ConversationTag])
async def get_conversation_tags(
    conversation_id: str,
    current_user: User = Depends(require_permissions(["messages:send"]))
):
    """
    Get all tags assigned to a conversation.
    
    Requires 'messages:send' permission (same as sending messages).
    """
    logger.info(f"🏷️ [GET_CONVERSATION_TAGS] Getting tags for conversation {conversation_id}")
    logger.info(f"👤 [GET_CONVERSATION_TAGS] User: {current_user.email} (ID: {current_user.id})")
    
    try:
        # Validate conversation exists
        conversation = await conversation_service.get_conversation(conversation_id)
        if not conversation:
            logger.error(f"❌ [GET_CONVERSATION_TAGS] Conversation not found: {conversation_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorCode.CONVERSATION_NOT_FOUND
            )
        
        # Get tags using service
        conversation_tags = await tag_service.get_conversation_tags(ObjectId(conversation_id))
        
        # Convert to response format matching frontend expectations
        tag_responses = []
        for conv_tag in conversation_tags:
            tag_summary = TagSummary(
                id=str(conv_tag["tag_id"]),
                name=conv_tag["tag_name"],
                slug=conv_tag.get("tag_slug", conv_tag["tag_name"].lower().replace(" ", "-")),
                display_name=conv_tag["tag_name"],
                category=conv_tag.get("tag_category", "general"),
                color=conv_tag["tag_color"],
                usage_count=0  # Not relevant for conversation tags
            )
            
            tag_responses.append(ConversationTag(
                tag=tag_summary,
                assigned_at=conv_tag["assigned_at"].isoformat(),
                assigned_by=str(conv_tag["assigned_by"]) if conv_tag.get("assigned_by") else None,
                auto_assigned=conv_tag.get("auto_assigned", False)
            ))
        
        logger.info(f"✅ [GET_CONVERSATION_TAGS] Found {len(tag_responses)} tags")
        
        return tag_responses
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ [GET_CONVERSATION_TAGS] Unexpected error: {str(e)}")
        raise handle_database_error(e, "get_conversation_tags", "conversation_tag")
