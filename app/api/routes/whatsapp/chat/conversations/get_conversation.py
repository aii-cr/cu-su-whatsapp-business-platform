"""Get conversation by ID endpoint."""

from fastapi import APIRouter, Depends, HTTPException, status
from bson import ObjectId

from app.schemas.whatsapp.chat import ConversationResponse
from app.services.auth import require_permissions
from app.db.models.auth import User
from app.db.client import database
from app.config.error_codes import ErrorCode

router = APIRouter()

@router.get("/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: str,
    current_user: User = Depends(require_permissions(["conversations:read"]))
):
    """
    Get conversation by ID.
    Requires 'conversations:read' permission.
    """
    db = database.db
    
    try:
        conversation = await db.conversations.find_one({"_id": ObjectId(conversation_id)})
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorCode.INVALID_CONVERSATION_ID
        )
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ErrorCode.CONVERSATION_NOT_FOUND
        )
    
    return ConversationResponse(**conversation) 