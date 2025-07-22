"""Update conversation endpoint."""

from fastapi import APIRouter, Depends, HTTPException, status
from datetime import datetime, timezone
from bson import ObjectId

from app.schemas.whatsapp.chat import ConversationUpdate, ConversationResponse
from app.services.auth import require_permissions
from app.db.models.auth import User
from app.db.client import database
from app.config.error_codes import ErrorCode
from app.core.logger import log_conversation_event

router = APIRouter()

@router.put("/{conversation_id}", response_model=ConversationResponse)
async def update_conversation(
    conversation_id: str,
    conversation_update: ConversationUpdate,
    current_user: User = Depends(require_permissions(["conversations:update"]))
):
    """
    Update conversation by ID.
    Requires 'conversations:update' permission.
    """
    db = database.db
    
    try:
        conversation_obj_id = ObjectId(conversation_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorCode.INVALID_CONVERSATION_ID
        )
    
    # Prepare update data
    update_data = conversation_update.model_dump(exclude_unset=True)
    if update_data:
        update_data["updated_at"] = datetime.now(timezone.utc)
        update_data["updated_by"] = current_user.id
        
        result = await db.conversations.update_one(
            {"_id": conversation_obj_id},
            {"$set": update_data}
        )
        
        if result.matched_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorCode.CONVERSATION_NOT_FOUND
            )
        
        # Log conversation update
        log_conversation_event(
            "updated",
            conversation_id,
            updated_by=str(current_user.id),
            changes=list(update_data.keys())
        )
    
    # Return updated conversation
    updated_conversation = await db.conversations.find_one({"_id": conversation_obj_id})
    return ConversationResponse(**updated_conversation) 