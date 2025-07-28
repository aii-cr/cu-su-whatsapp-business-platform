"""Get conversation messages endpoint."""

from fastapi import APIRouter, Depends, HTTPException, status
from bson import ObjectId

from app.services.auth import require_permissions, check_user_permission
from app.db.models.auth import User
from app.db.client import database
from app.config.error_codes import ErrorCode
from app.core.logger import logger
from app.schemas.whatsapp.chat.message_out import MessageListResponse, MessageResponse

router = APIRouter()

@router.get("/conversation/{conversation_id}", response_model=MessageListResponse)
async def get_conversation_messages(
    conversation_id: str,
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(require_permissions(["messages:read"]))
):
    """
    Get messages for a specific conversation.
    Requires 'messages:read' permission.
    """
    db = database.db
    
    try:
        # Verify conversation exists and user has access
        conversation = await db.conversations.find_one({
            "_id": ObjectId(conversation_id)
        })
        
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorCode.CONVERSATION_NOT_FOUND
            )
        
        # Check access permissions
        if (conversation.get("assigned_agent_id") != current_user.id and 
            not current_user.is_super_admin and
            not await check_user_permission(current_user.id, "messages:read_all")):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=ErrorCode.CONVERSATION_ACCESS_DENIED
            )
        
        # Get messages in chronological order (oldest first)
        messages = await db.messages.find(
            {"conversation_id": ObjectId(conversation_id)}
        ).sort("timestamp", 1).skip(offset).limit(limit).to_list(limit)
        
        # Count total
        total = await db.messages.count_documents(
            {"conversation_id": ObjectId(conversation_id)}
        )
        
        return MessageListResponse(
            messages=[MessageResponse(**msg) for msg in messages],
            total=total,
            limit=limit,
            offset=offset
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get conversation messages: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorCode.INTERNAL_SERVER_ERROR
        ) 