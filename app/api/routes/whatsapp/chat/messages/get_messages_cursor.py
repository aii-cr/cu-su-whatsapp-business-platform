"""Get messages with cursor-based pagination endpoint."""

from fastapi import APIRouter, Depends, HTTPException, Query, status, Response
from typing import Optional
from pydantic import BaseModel, Field
from bson import ObjectId

from app.config.error_codes import ErrorCode, get_error_response
from app.core.logger import logger
from app.services.auth import require_permissions, check_user_permission
from app.db.models.auth import User
from app.schemas.whatsapp.chat.message_out import MessageResponse
from app.services import conversation_service
from app.services.whatsapp.message.cursor_message_service import cursor_message_service
from app.core.error_handling import handle_database_error
from app.core.middleware import get_correlation_id

router = APIRouter()

class MessagesCursorResponse(BaseModel):
    """Response model for cursor-based message pagination."""
    messages: list[MessageResponse] = Field(..., description="List of messages ordered by _id desc")
    next_cursor: Optional[str] = Field(None, description="Cursor for next page (ObjectId of last message)")
    has_more: bool = Field(..., description="Whether there are more messages to load")
    anchor: str = Field("desc", description="Sort order anchor")
    cache_hit: bool = Field(False, description="Whether response was served from cache")

@router.get("/cursor", response_model=MessagesCursorResponse)
async def get_messages_cursor(
    chatId: str = Query(..., description="Conversation ID"),
    limit: int = Query(50, ge=1, le=100, description="Number of messages to return (max 100)"),
    before: Optional[str] = Query(None, description="Cursor for pagination (ObjectId)"),
    current_user: User = Depends(require_permissions(["messages:read"])),
    response: Response = None
):
    """
    Get messages for a conversation with cursor-based pagination.
    
    This endpoint provides efficient pagination for chat interfaces:
    - Uses cursor-based pagination (ObjectId) for consistent performance
    - Supports Redis caching for the latest messages
    - Returns messages in descending order (newest first)
    - Optimized for infinite scroll in chat applications
    
    Args:
        chatId: ID of the conversation (required)
        limit: Number of messages to return (1-100)
        before: Cursor for pagination (ObjectId of last message from previous page)
        current_user: Current authenticated user
        
    Returns:
        Messages with pagination info and cache status
    """
    correlation_id = get_correlation_id()
    
    try:
        logger.info(
            f"🚀 [GET_MESSAGES_CURSOR] Loading messages for conversation {chatId}",
            extra={
                "conversation_id": chatId,
                "limit": limit,
                "before": before,
                "user_id": str(current_user.id),
                "correlation_id": correlation_id
            }
        )
        
        # Validate conversation_id format
        try:
            ObjectId(chatId)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=get_error_response(ErrorCode.INVALID_CONVERSATION_ID)
            )
        
        # Validate before cursor if provided
        if before:
            try:
                ObjectId(before)
            except Exception:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=get_error_response(ErrorCode.INVALID_CURSOR)
                )
        
        # Get conversation to verify access
        conversation = await conversation_service.get_conversation(chatId)
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=get_error_response(ErrorCode.CONVERSATION_NOT_FOUND)
            )
        
        # Check access permissions
        if not current_user.is_super_admin:
            if (conversation.get("assigned_agent_id") != current_user.id and 
                not await check_user_permission(current_user.id, "messages:read_all")):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=get_error_response(ErrorCode.CONVERSATION_ACCESS_DENIED)
                )
        
        # Get messages using cursor service
        result = await cursor_message_service.get_messages_cursor(
            conversation_id=chatId,
            limit=limit,
            before=before,
            user_id=str(current_user.id)
        )
        

        # Set cache headers for the latest messages (without before cursor)
        if not before and result.get("cache_hit"):
            response.headers["Cache-Control"] = "private, max-age=30, must-revalidate"
            response.headers["ETag"] = f'"{result.get("etag", "")}"'
        
        logger.info(
            f"✅ [GET_MESSAGES_CURSOR] Retrieved {len(result['messages'])} messages for conversation {chatId}",
            extra={
                "conversation_id": chatId,
                "message_count": len(result["messages"]),
                "has_more": result["has_more"],
                "cache_hit": result.get("cache_hit", False),
                "user_id": str(current_user.id),
                "correlation_id": correlation_id
            }
        )
        
        # Transform messages through the MessageResponse schema
        transformed_messages = []
        for message_data in result["messages"]:
            try:
                # Transform the message data through the schema
                message_response = MessageResponse(**message_data)
                transformed_messages.append(message_response)
            except Exception as e:
                logger.warning(f"⚠️ [GET_MESSAGES_CURSOR] Failed to transform message {message_data.get('_id', 'unknown')}: {str(e)}")
                # Include the raw message if transformation fails
                transformed_messages.append(message_data)
        
        return MessagesCursorResponse(
            messages=transformed_messages,
            next_cursor=result["next_cursor"],
            has_more=result["has_more"],
            anchor="desc",
            cache_hit=result.get("cache_hit", False)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"❌ [GET_MESSAGES_CURSOR] Error retrieving messages for conversation {chatId}: {str(e)}",
            extra={
                "conversation_id": chatId,
                "user_id": str(current_user.id),
                "correlation_id": correlation_id,
                "error": str(e)
            }
        )
        raise handle_database_error(e, "get_messages_cursor", "messages")

@router.get("/cursor/around", response_model=MessagesCursorResponse)
async def get_messages_around(
    chatId: str = Query(..., description="Conversation ID"),
    anchorId: str = Query(..., description="Message ID to center around"),
    limit: int = Query(25, ge=1, le=50, description="Number of messages to return (max 50)"),
    current_user: User = Depends(require_permissions(["messages:read"]))
):
    """
    Get messages around a specific message ID.
    
    This endpoint is useful for jumping to a specific message in a conversation
    and loading context around it.
    
    Args:
        chatId: ID of the conversation (required)
        anchorId: Message ID to center around (required)
        limit: Number of messages to return (1-50)
        current_user: Current authenticated user
        
    Returns:
        Messages with pagination info
    """
    correlation_id = get_correlation_id()
    
    try:
        logger.info(
            f"🚀 [GET_MESSAGES_AROUND] Loading messages around {anchorId} for conversation {chatId}",
            extra={
                "conversation_id": chatId,
                "anchor_id": anchorId,
                "limit": limit,
                "user_id": str(current_user.id),
                "correlation_id": correlation_id
            }
        )
        
        # Validate IDs
        try:
            ObjectId(chatId)
            ObjectId(anchorId)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=get_error_response(ErrorCode.INVALID_ID)
            )
        
        # Get conversation to verify access
        conversation = await conversation_service.get_conversation(chatId)
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=get_error_response(ErrorCode.CONVERSATION_NOT_FOUND)
            )
        
        # Check access permissions
        if not current_user.is_super_admin:
            if (conversation.get("assigned_agent_id") != current_user.id and 
                not await check_user_permission(current_user.id, "messages:read_all")):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=get_error_response(ErrorCode.CONVERSATION_ACCESS_DENIED)
                )
        
        # Get messages around anchor
        result = await cursor_message_service.get_messages_around(
            conversation_id=chatId,
            anchor_id=anchorId,
            limit=limit,
            user_id=str(current_user.id)
        )
        
        logger.info(
            f"✅ [GET_MESSAGES_AROUND] Retrieved {len(result['messages'])} messages around {anchorId}",
            extra={
                "conversation_id": chatId,
                "anchor_id": anchorId,
                "message_count": len(result["messages"]),
                "has_more": result["has_more"],
                "user_id": str(current_user.id),
                "correlation_id": correlation_id
            }
        )
        
        # Transform messages through the MessageResponse schema
        transformed_messages = []
        for message_data in result["messages"]:
            try:
                # Transform the message data through the schema
                message_response = MessageResponse(**message_data)
                transformed_messages.append(message_response)
            except Exception as e:
                logger.warning(f"⚠️ [GET_MESSAGES_AROUND] Failed to transform message {message_data.get('_id', 'unknown')}: {str(e)}")
                # Include the raw message if transformation fails
                transformed_messages.append(message_data)
        
        return MessagesCursorResponse(
            messages=transformed_messages,
            next_cursor=result["next_cursor"],
            has_more=result["has_more"],
            anchor="desc",
            cache_hit=False  # Around queries are not cached
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"❌ [GET_MESSAGES_AROUND] Error retrieving messages around {anchorId}: {str(e)}",
            extra={
                "conversation_id": chatId,
                "anchor_id": anchorId,
                "user_id": str(current_user.id),
                "correlation_id": correlation_id,
                "error": str(e)
            }
        )
        raise handle_database_error(e, "get_messages_around", "messages")
