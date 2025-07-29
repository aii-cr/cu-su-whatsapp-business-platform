"""Get messages for a conversation endpoint."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import Optional

from app.config.error_codes import ErrorCode
from app.core.logger import logger
from app.services.auth import require_permissions, check_user_permission
from app.db.models.auth import User
from app.schemas.whatsapp.chat.message_out import MessageListResponse
from app.services import message_service, conversation_service
from app.core.error_handling import handle_database_error

router = APIRouter()

@router.get("/conversation/{conversation_id}", response_model=MessageListResponse)
async def get_messages(
    conversation_id: str,
    limit: int = Query(50, ge=1, le=200, description="Number of messages to return"),
    offset: int = Query(0, ge=0, description="Number of messages to skip"),
    current_user: User = Depends(require_permissions(["messages:read"])),
):
    """
    Get messages for a specific conversation.
    
    Args:
        conversation_id: ID of the conversation
        limit: Number of messages to return (max 200)
        offset: Number of messages to skip for pagination
        current_user: Current authenticated user
        
    Returns:
        List of messages with pagination info
    """
    try:
        # Get conversation to verify access
        conversation = await conversation_service.get_conversation(conversation_id)
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorCode.CONVERSATION_NOT_FOUND
            )
        
        # Check access permissions
        if not current_user.is_super_admin:
            if (conversation.get("assigned_agent_id") != current_user.id and 
                not await check_user_permission(current_user.id, "messages:read_all")):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=ErrorCode.CONVERSATION_ACCESS_DENIED
                )
        
        # Get messages using service
        result = await message_service.get_conversation_messages(
            conversation_id=conversation_id,
            limit=limit,
            offset=offset,
            sort_by="timestamp",
            sort_order="asc"
        )
        
        logger.info(f"Retrieved {len(result['messages'])} messages for conversation {conversation_id}")
        
        return MessageListResponse(
            messages=result["messages"],
            total=result["total"],
            page=result["page"],
            per_page=result["per_page"],
            pages=result["pages"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving messages for conversation {conversation_id}: {str(e)}")
        raise handle_database_error(e, "get_messages", "messages") 