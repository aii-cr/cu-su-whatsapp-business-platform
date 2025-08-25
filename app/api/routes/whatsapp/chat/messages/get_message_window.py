"""Get message window endpoint - Optimized with Redis caching and cursor-based pagination."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import Optional
from pydantic import BaseModel

from app.config.error_codes import ErrorCode, get_error_response
from app.core.logger import logger
from app.services.auth import require_permissions
from app.db.models.auth import User
from app.schemas.whatsapp.chat.message_out import MessageResponse
from app.services.whatsapp.message.cached_message_service import cached_message_service
from app.core.error_handling import handle_database_error
from app.core.middleware import get_correlation_id

router = APIRouter()

class MessageWindowResponse(BaseModel):
    """Response model for message window with cursor-based pagination."""
    messages: list[MessageResponse]
    has_more: bool
    next_cursor: Optional[str]
    prev_cursor: Optional[str]
    cache_hit: bool
    total_messages: Optional[int] = None
    window_info: dict

@router.get("/window", response_model=MessageWindowResponse)
async def get_message_window(
    conversation_id: str,
    anchor: str = Query("latest", description="Message ID to start from or 'latest' for most recent"),
    direction: str = Query("before", regex="^(before|after)$", description="Direction: 'before' (older) or 'after' (newer)"),
    limit: int = Query(50, ge=1, le=100, description="Number of messages to return"),
    current_user: User = Depends(require_permissions(["messages:read"]))
):
    """
    Get a window of messages with cursor-based pagination and Redis caching.
    
    This endpoint provides fast message loading for chat interfaces:
    - Uses Redis caching for sub-second response times
    - Supports cursor-based pagination for smooth scrolling
    - Automatically handles cache invalidation
    - Optimized for WhatsApp-like chat experience
    
    Args:
        conversation_id: ID of the conversation
        anchor: Starting point - message ID or "latest" for most recent
        direction: "before" for older messages, "after" for newer
        limit: Number of messages (1-100)
        current_user: Current authenticated user
        
    Returns:
        Message window with pagination info and cache status
    """
    correlation_id = get_correlation_id()
    
    try:
        logger.info(
            f"🚀 [GET_MESSAGE_WINDOW] Loading message window for conversation {conversation_id}",
            extra={
                "conversation_id": conversation_id,
                "anchor": anchor,
                "direction": direction,
                "limit": limit,
                "user_id": str(current_user.id),
                "correlation_id": correlation_id
            }
        )
        
        # Get message window using cached service
        result = await cached_message_service.get_message_window(
            user_id=str(current_user.id),
            conversation_id=conversation_id,
            anchor=anchor,
            direction=direction,
            limit=limit,
            use_cache=True
        )
        
        if not result["messages"] and anchor != "latest":
            # If no messages found with specific anchor, it might be invalid
            logger.warning(
                f"❌ [GET_MESSAGE_WINDOW] No messages found for anchor {anchor}",
                extra={
                    "conversation_id": conversation_id,
                    "anchor": anchor,
                    "user_id": str(current_user.id),
                    "correlation_id": correlation_id
                }
            )
        
        # Calculate window info for debugging and monitoring
        window_info = {
            "anchor": anchor,
            "direction": direction,
            "limit": limit,
            "actual_count": len(result["messages"]),
            "cache_hit": result["cache_hit"],
            "has_more": result["has_more"]
        }
        
        logger.info(
            f"✅ [GET_MESSAGE_WINDOW] Returned {len(result['messages'])} messages (cache_hit: {result['cache_hit']})",
            extra={
                "conversation_id": conversation_id,
                "messages_count": len(result["messages"]),
                "cache_hit": result["cache_hit"],
                "has_more": result["has_more"],
                "user_id": str(current_user.id),
                "correlation_id": correlation_id
            }
        )
        
        return MessageWindowResponse(
            messages=[MessageResponse(**msg) for msg in result["messages"]],
            has_more=result["has_more"],
            next_cursor=result["next_cursor"],
            prev_cursor=result.get("prev_cursor"),
            cache_hit=result["cache_hit"],
            window_info=window_info
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"💥 [GET_MESSAGE_WINDOW] Error loading message window: {str(e)}",
            extra={
                "conversation_id": conversation_id,
                "user_id": str(current_user.id),
                "error": str(e),
                "correlation_id": correlation_id
            },
            exc_info=True
        )
        raise handle_database_error(e, "get_message_window", "messages")


@router.get("/{conversation_id}/recent", response_model=MessageWindowResponse)
async def get_recent_messages(
    conversation_id: str,
    limit: int = Query(50, ge=1, le=100, description="Number of recent messages to return"),
    current_user: User = Depends(require_permissions(["messages:read"]))
):
    """
    Get recent messages for a conversation - optimized for chat entry.
    
    This is the main endpoint for opening a chat quickly.
    Uses aggressive caching for sub-second response times.
    
    Args:
        conversation_id: ID of the conversation
        limit: Number of recent messages (1-100)
        current_user: Current authenticated user
        
    Returns:
        Recent messages with cache status
    """
    correlation_id = get_correlation_id()
    
    try:
        logger.info(
            f"🚀 [GET_RECENT_MESSAGES] Loading recent messages for conversation {conversation_id}",
            extra={
                "conversation_id": conversation_id,
                "limit": limit,
                "user_id": str(current_user.id),
                "correlation_id": correlation_id
            }
        )
        
        # Get recent messages using cached service
        result = await cached_message_service.get_recent_messages_optimized(
            user_id=str(current_user.id),
            conversation_id=conversation_id,
            limit=limit
        )
        
        # Calculate window info
        window_info = {
            "anchor": "latest",
            "direction": "before",
            "limit": limit,
            "actual_count": len(result["messages"]),
            "cache_hit": result["cache_hit"],
            "has_more": result["has_more"]
        }
        
        logger.info(
            f"✅ [GET_RECENT_MESSAGES] Returned {len(result['messages'])} messages (cache_hit: {result['cache_hit']})",
            extra={
                "conversation_id": conversation_id,
                "messages_count": len(result["messages"]),
                "cache_hit": result["cache_hit"],
                "user_id": str(current_user.id),
                "correlation_id": correlation_id
            }
        )
        
        return MessageWindowResponse(
            messages=[MessageResponse(**msg) for msg in result["messages"]],
            has_more=result["has_more"],
            next_cursor=result["next_cursor"],
            prev_cursor=result.get("prev_cursor"),
            cache_hit=result["cache_hit"],
            window_info=window_info
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"💥 [GET_RECENT_MESSAGES] Error loading recent messages: {str(e)}",
            extra={
                "conversation_id": conversation_id,
                "user_id": str(current_user.id),
                "error": str(e),
                "correlation_id": correlation_id
            },
            exc_info=True
        )
        raise handle_database_error(e, "get_recent_messages", "messages")


@router.get("/{conversation_id}/older", response_model=MessageWindowResponse)
async def get_older_messages(
    conversation_id: str,
    cursor: str = Query(..., description="Message ID cursor for pagination"),
    limit: int = Query(50, ge=1, le=100, description="Number of older messages to return"),
    current_user: User = Depends(require_permissions(["messages:read"]))
):
    """
    Get older messages for scroll-up lazy loading.
    
    This endpoint is specifically for loading older messages when user scrolls up.
    Uses cursor-based pagination for smooth performance.
    
    Args:
        conversation_id: ID of the conversation
        cursor: Message ID to start from (older messages)
        limit: Number of messages (1-100)
        current_user: Current authenticated user
        
    Returns:
        Older messages with pagination info
    """
    correlation_id = get_correlation_id()
    
    try:
        logger.info(
            f"🚀 [GET_OLDER_MESSAGES] Loading older messages for conversation {conversation_id}",
            extra={
                "conversation_id": conversation_id,
                "cursor": cursor,
                "limit": limit,
                "user_id": str(current_user.id),
                "correlation_id": correlation_id
            }
        )
        
        # Get older messages using cached service
        result = await cached_message_service.get_older_messages(
            user_id=str(current_user.id),
            conversation_id=conversation_id,
            cursor=cursor,
            limit=limit
        )
        
        # Calculate window info
        window_info = {
            "anchor": cursor,
            "direction": "before",
            "limit": limit,
            "actual_count": len(result["messages"]),
            "cache_hit": result["cache_hit"],
            "has_more": result["has_more"]
        }
        
        logger.info(
            f"✅ [GET_OLDER_MESSAGES] Returned {len(result['messages'])} messages (cache_hit: {result['cache_hit']})",
            extra={
                "conversation_id": conversation_id,
                "messages_count": len(result["messages"]),
                "cache_hit": result["cache_hit"],
                "user_id": str(current_user.id),
                "correlation_id": correlation_id
            }
        )
        
        return MessageWindowResponse(
            messages=[MessageResponse(**msg) for msg in result["messages"]],
            has_more=result["has_more"],
            next_cursor=result["next_cursor"],
            prev_cursor=result.get("prev_cursor"),
            cache_hit=result["cache_hit"],
            window_info=window_info
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"💥 [GET_OLDER_MESSAGES] Error loading older messages: {str(e)}",
            extra={
                "conversation_id": conversation_id,
                "user_id": str(current_user.id),
                "error": str(e),
                "correlation_id": correlation_id
            },
            exc_info=True
        )
        raise handle_database_error(e, "get_older_messages", "messages")
