"""Mark messages as read endpoint."""

from fastapi import APIRouter, HTTPException, status, Depends, Request
from typing import List
from datetime import datetime, timezone
from bson import ObjectId

from app.services.auth.utils.session_auth import get_current_user
from app.db.client import database
from app.db.models.auth.user import User
from app.db.models.whatsapp.chat.message import Message, MessageStatus
from app.schemas.whatsapp.chat.message import MessageReadRequest, MessageReadResponse
from app.core.logger import logger
from app.core.error_handling import handle_database_error
from app.services.websocket.websocket_service import websocket_service

router = APIRouter()

@router.post("/mark-read", response_model=MessageReadResponse)
async def mark_messages_read(
    request_data: MessageReadRequest,
    current_user: User = Depends(get_current_user),
    request: Request = None
):
    """
    Mark inbound messages as read when an agent views them in the conversation interface.
    This endpoint is called when the agent enters the conversation view and messages are visible.
    """
    try:
        db = await database._get_db()
        conversation_id = ObjectId(request_data.conversation_id)
        
        # Verify the user is the assigned agent for this conversation
        conversation = await db.conversations.find_one({
            "_id": conversation_id,
            "assigned_agent_id": current_user.id
        })
        
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the assigned agent can mark messages as read"
            )
        
        # Find all inbound messages in the conversation that are not yet read
        # Only mark messages as read if they are inbound (from customer)
        unread_messages = await db.messages.find({
            "conversation_id": conversation_id,
            "direction": "inbound",
            "status": {"$in": ["received", "delivered"]}  # Only mark unread messages
        }).to_list(length=None)
        
        if not unread_messages:
            logger.info(f"No unread messages found for conversation {conversation_id}")
            return MessageReadResponse(
                conversation_id=str(conversation_id),
                messages_marked_read=0,
                timestamp=datetime.now(timezone.utc)
            )
        
        # Update all unread inbound messages to read status
        now = datetime.now(timezone.utc)
        message_ids = [msg["_id"] for msg in unread_messages]
        
        result = await db.messages.update_many(
            {
                "_id": {"$in": message_ids},
                "conversation_id": conversation_id,
                "direction": "inbound",
                "status": {"$in": ["received", "delivered"]}
            },
            {
                "$set": {
                    "status": MessageStatus.READ,
                    "read_at": now,
                    "updated_at": now
                }
            }
        )
        
        messages_marked_read = result.modified_count
        
        if messages_marked_read > 0:
            logger.info(f"Marked {messages_marked_read} messages as read in conversation {conversation_id} by user {current_user.email}")
            
            # Notify other users in the conversation about the read status updates
            await websocket_service.notify_message_read_status(
                str(conversation_id),
                message_ids=[str(msg_id) for msg_id in message_ids],
                read_by_user_id=str(current_user.id),
                read_by_user_name=current_user.first_name + " " + current_user.last_name
            )
            
            # Reset unread count for this user and conversation
            await websocket_service.reset_unread_count_for_user(str(current_user.id), str(conversation_id))
        
        return MessageReadResponse(
            conversation_id=str(conversation_id),
            messages_marked_read=messages_marked_read,
            timestamp=now
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error marking messages as read: {str(e)}")
        raise handle_database_error(e, "mark_messages_read", "message")
