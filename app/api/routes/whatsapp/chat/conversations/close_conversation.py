from datetime import datetime, timezone

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, status

from app.config.error_codes import ErrorCode
from app.core.logger import logger
from app.core.middleware import get_correlation_id
from app.db.client import database
from app.db.models.auth import User
from app.schemas.whatsapp.chat.conversation import ConversationClose, ConversationResponse
from app.services import audit_service
from app.services.auth import require_permissions

router = APIRouter()

@router.post("/{conversation_id}/close", response_model=ConversationResponse)
async def close_conversation(
    conversation_id: str,
    close_data: ConversationClose,
    current_user: User = Depends(require_permissions(["conversations:close"])),
):
    """
    Close a conversation by ID.
    Requires 'conversations:close' permission.
    """
    try:
        conversation_obj_id = ObjectId(conversation_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=ErrorCode.INVALID_CONVERSATION_ID
        )

    try:
        db = database.db
        
        # Get current conversation
        conversation = await db.conversations.find_one({"_id": conversation_obj_id})
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=ErrorCode.CONVERSATION_NOT_FOUND
            )
        
        # Check if conversation is already closed
        if conversation.get("status") == "resolved":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail="Conversation is already closed"
            )
        
        # Prepare update data
        update_data = {
            "status": "resolved",
            "session_ended_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
            "updated_by": current_user.id
        }
        
        # Add optional fields if provided
        if close_data.resolution_notes:
            update_data["feedback_comment"] = close_data.resolution_notes
        
        if close_data.satisfaction_rating:
            update_data["satisfaction_rating"] = close_data.satisfaction_rating
        
        if close_data.feedback_comment:
            update_data["feedback_comment"] = close_data.feedback_comment
        
        if close_data.tags:
            # Merge with existing tags
            existing_tags = conversation.get("tags", [])
            new_tags = [tag for tag in close_data.tags if tag not in existing_tags]
            if new_tags:
                update_data["tags"] = existing_tags + new_tags
        
        # Update conversation
        result = await db.conversations.update_one(
            {"_id": conversation_obj_id}, {"$set": update_data}
        )
        
        if result.matched_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=ErrorCode.CONVERSATION_NOT_FOUND
            )
        
        # Get updated conversation for response
        updated_conversation = await db.conversations.find_one({"_id": conversation_obj_id})
        
        # ===== AUDIT LOGGING =====
        correlation_id = get_correlation_id()
        await audit_service.log_conversation_closed(
            actor_id=str(current_user.id),
            actor_name=current_user.name or current_user.email,
            conversation_id=conversation_id,
            customer_phone=conversation.get("customer_phone"),
            department_id=str(conversation.get("department_id")) if conversation.get("department_id") else None,
            reason=close_data.reason,
            resolution=close_data.resolution_notes,
            correlation_id=correlation_id
        )
        
        logger.info(f"Conversation {conversation_id} closed by user {current_user.id}")
        
        return ConversationResponse(**updated_conversation)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error closing conversation {conversation_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to close conversation"
        ) 