"""
WebSocket routes for real-time messaging updates.
Handles WebSocket connections and subscriptions for live chat functionality.
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, status, Request, Depends
from typing import Optional
import json
from datetime import datetime, timezone

from app.core.logger import logger
from app.services.websocket.websocket_service import manager, websocket_service
from app.db.client import database
from bson import ObjectId
from app.services.auth.utils.session_auth import get_current_user
from app.db.models.auth.user import User

router = APIRouter(prefix="/ws", tags=["WebSocket"])

@router.websocket("/chat/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    """
    WebSocket endpoint for real-time chat updates.
    
    Args:
        websocket: WebSocket connection
        user_id: User ID for the connection
    """
    try:
        # Accept the WebSocket connection first
        await websocket.accept()
        
        # Validate user_id format (basic validation)
        if not user_id or len(user_id) < 10:  # Basic validation
            logger.warning(f"🔌 [WEBSOCKET] Invalid user_id format: {user_id}")
            await websocket.close(code=4003, reason="Invalid user ID")
            return
        
        # Connect to manager
        await manager.connect(websocket, user_id)
        logger.info(f"🔌 [WEBSOCKET] Connected for user {user_id}")
        logger.info(f"🔌 [WEBSOCKET] Total active connections: {len(manager.active_connections)}")
        
        while True:
            # Wait for messages from the client
            data = await websocket.receive_text()
            message = json.loads(data)
            
            logger.info(f"📨 [WEBSOCKET] Received message from user {user_id}: {message}")
            
            # Handle different message types
            await handle_websocket_message(user_id, message)
            
    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)
        logger.info(f"🔌 [WEBSOCKET] Disconnected for user {user_id}")
    except Exception as e:
        logger.error(f"❌ [WEBSOCKET] Error for user {user_id}: {str(e)}")
        manager.disconnect(websocket, user_id)

@router.websocket("/dashboard/{user_id}")
async def dashboard_websocket_endpoint(websocket: WebSocket, user_id: str):
    """
    WebSocket endpoint for real-time dashboard updates.
    
    Args:
        websocket: WebSocket connection
        user_id: User ID for the connection
    """
    try:
        # Accept the WebSocket connection first
        await websocket.accept()
        
        # Validate user_id format (basic validation)
        if not user_id or len(user_id) < 10:  # Basic validation
            logger.warning(f"🏠 [DASHBOARD_WS] Invalid user_id format: {user_id}")
            await websocket.close(code=4003, reason="Invalid user ID")
            return
        
        # Connect to manager
        await manager.connect(websocket, user_id)
        
        # Automatically subscribe to dashboard updates
        await manager.subscribe_to_dashboard(user_id)
        logger.info(f"🏠 [DASHBOARD_WS] Connected and subscribed to dashboard for user {user_id}")
        logger.info(f"🏠 [DASHBOARD_WS] Total dashboard subscribers: {len(manager.dashboard_subscribers)}")
        
        # Calculate and send current unread counts from database
        unread_counts = await calculate_unread_counts_from_database(user_id)
        await manager.send_personal_message({
            "type": "initial_unread_counts",
            "unread_counts": unread_counts,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }, user_id)
        
        while True:
            # Wait for messages from the client
            data = await websocket.receive_text()
            message = json.loads(data)
            
            logger.info(f"📨 [DASHBOARD_WS] Received message from user {user_id}: {message}")
            
            # Handle dashboard-specific message types
            await handle_dashboard_websocket_message(user_id, message)
            
    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)
        logger.info(f"🏠 [DASHBOARD_WS] Disconnected for user {user_id}")
    except Exception as e:
        logger.error(f"❌ [DASHBOARD_WS] Error for user {user_id}: {str(e)}")
        manager.disconnect(websocket, user_id)
        

async def handle_websocket_message(user_id: str, message: dict):
    """
    Handle incoming WebSocket messages from clients.
    
    Args:
        user_id: User ID sending the message
        message: Message data from client
    """
    try:
        message_type = message.get("type")
        
        if message_type == "subscribe_conversation":
            conversation_id = message.get("conversation_id")
            logger.info(f"🔔 [WEBSOCKET] User {user_id} subscribing to conversation {conversation_id}")
            if conversation_id:
                subscription_needed = await manager.subscribe_to_conversation(user_id, conversation_id)
                
                if subscription_needed:
                    logger.info(f"✅ [WEBSOCKET] User {user_id} successfully subscribed to conversation {conversation_id}")
                    await manager.send_personal_message({
                        "type": "subscription_confirmed",
                        "conversation_id": conversation_id,
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    }, user_id)
                else:
                    logger.info(f"📋 [WEBSOCKET] User {user_id} subscription to conversation {conversation_id} not needed (already subscribed)")
                    # Optionally send a different confirmation or no message at all
                    await manager.send_personal_message({
                        "type": "subscription_already_active",
                        "conversation_id": conversation_id,
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    }, user_id)
            else:
                logger.warning(f"❌ [WEBSOCKET] User {user_id} attempted to subscribe without conversation_id")
        
        elif message_type == "unsubscribe_conversation":
            conversation_id = message.get("conversation_id")
            if conversation_id:
                await manager.unsubscribe_from_conversation(user_id, conversation_id)
                await manager.send_personal_message({
                    "type": "unsubscription_confirmed",
                    "conversation_id": conversation_id,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }, user_id)
        
        elif message_type == "mark_messages_read":
            conversation_id = message.get("conversation_id")
            if conversation_id:
                await handle_mark_messages_read(user_id, conversation_id)
        
        elif message_type == "typing_start":
            conversation_id = message.get("conversation_id")
            if conversation_id:
                await websocket_service.notify_user_activity(user_id, {
                    "type": "typing_start",
                    "conversation_id": conversation_id
                })
        
        elif message_type == "typing_stop":
            conversation_id = message.get("conversation_id")
            if conversation_id:
                await websocket_service.notify_user_activity(user_id, {
                    "type": "typing_stop",
                    "conversation_id": conversation_id
                })
        
        elif message_type == "subscribe_dashboard":
            await manager.subscribe_to_dashboard(user_id)
            await manager.send_personal_message({
                "type": "dashboard_subscription_confirmed",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }, user_id)
        
        elif message_type == "unsubscribe_dashboard":
            await manager.unsubscribe_from_dashboard(user_id)
            await manager.send_personal_message({
                "type": "dashboard_unsubscription_confirmed",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }, user_id)
        
        elif message_type == "mark_conversation_read":
            conversation_id = message.get("conversation_id")
            if conversation_id:
                await websocket_service.reset_unread_count_for_user(user_id, conversation_id)
                logger.info(f"📖 [WEBSOCKET] User {user_id} marked conversation {conversation_id} as read")
        
        elif message_type == "ping":
            # Respond to ping with pong
            await manager.send_personal_message({
                "type": "pong",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }, user_id)
        
        else:
            logger.warning(f"Unknown WebSocket message type: {message_type} from user {user_id}")
            
    except Exception as e:
        logger.error(f"Error handling WebSocket message from user {user_id}: {str(e)}")
        # Send error message to client
        try:
            await manager.send_personal_message({
                "type": "error",
                "message": "Internal server error",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }, user_id)
        except Exception:
            pass  # Ignore errors when sending error messages


async def handle_mark_messages_read(user_id: str, conversation_id: str):
    """
    Handle marking messages as read via WebSocket.
    
    Args:
        user_id: User ID marking messages as read
        conversation_id: Conversation ID to mark messages as read
    """
    try:
        from app.db.client import database
        from app.db.models.whatsapp.chat.message import MessageStatus
        from bson import ObjectId
        
        # Get database connection
        db = await database.get_database()
        
        # Verify the user is the assigned agent for this conversation
        conversation = await db.conversations.find_one({
            "_id": ObjectId(conversation_id),
            "assigned_agent_id": ObjectId(user_id)
        })
        
        if not conversation:
            logger.warning(f"❌ [WEBSOCKET] User {user_id} attempted to mark messages as read but is not the assigned agent for conversation {conversation_id}")
            return
        
        # Find all inbound messages in the conversation that are not yet read
        unread_messages = await db.messages.find({
            "conversation_id": ObjectId(conversation_id),
            "direction": "inbound",
            "status": {"$in": ["received", "delivered"]}
        }).to_list(length=None)
        
        if not unread_messages:
            logger.info(f"📋 [WEBSOCKET] No unread messages found for conversation {conversation_id}")
            return
        
        # Update all unread inbound messages to read status
        now = datetime.now(timezone.utc)
        message_ids = [msg["_id"] for msg in unread_messages]
        
        result = await db.messages.update_many(
            {
                "_id": {"$in": message_ids},
                "conversation_id": ObjectId(conversation_id),
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
            logger.info(f"✅ [WEBSOCKET] Marked {messages_marked_read} messages as read in conversation {conversation_id} by user {user_id}")
            
            # Notify other users in the conversation about the read status updates
            await websocket_service.notify_message_read_status(
                conversation_id,
                message_ids=[str(msg_id) for msg_id in message_ids],
                read_by_user_id=user_id,
                read_by_user_name="Agent"  # We could get this from user data if needed
            )
            
            # Reset unread count for this user and conversation
            await websocket_service.reset_unread_count_for_user(user_id, conversation_id)
            
            # Send confirmation to the user
            await manager.send_personal_message({
                "type": "messages_read_confirmed",
                "conversation_id": conversation_id,
                "messages_marked_read": messages_marked_read,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }, user_id)
            
            # Also notify about conversation update to refresh UI
            await websocket_service.notify_conversation_update(conversation_id, {
                "last_read_at": now.isoformat(),
                "unread_count": 0
            })
        
    except Exception as e:
        logger.error(f"❌ [WEBSOCKET] Error marking messages as read for user {user_id} in conversation {conversation_id}: {str(e)}")
        
        # Send error message to client
        try:
            await manager.send_personal_message({
                "type": "error",
                "message": "Failed to mark messages as read",
                "conversation_id": conversation_id,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }, user_id)
        except Exception:
            pass  # Ignore errors when sending error messages


async def handle_dashboard_websocket_message(user_id: str, message: dict):
    """
    Handle incoming WebSocket messages from dashboard clients.
    
    Args:
        user_id: User ID sending the message
        message: Message data from client
    """
    try:
        message_type = message.get("type")
        
        if message_type == "subscribe_dashboard":
            await manager.subscribe_to_dashboard(user_id)
            await manager.send_personal_message({
                "type": "dashboard_subscription_confirmed",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }, user_id)
            logger.info(f"🏠 [DASHBOARD_WS] User {user_id} subscribed to dashboard updates")
        
        elif message_type == "unsubscribe_dashboard":
            await manager.unsubscribe_from_dashboard(user_id)
            await manager.send_personal_message({
                "type": "dashboard_unsubscription_confirmed",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }, user_id)
            logger.info(f"🏠 [DASHBOARD_WS] User {user_id} unsubscribed from dashboard updates")
        
        elif message_type == "mark_conversation_read":
            conversation_id = message.get("conversation_id")
            if conversation_id:
                await websocket_service.reset_unread_count_for_user(user_id, conversation_id)
                logger.info(f"📖 [DASHBOARD_WS] User {user_id} marked conversation {conversation_id} as read")
        
        elif message_type == "request_stats_update":
            # Trigger a stats update broadcast
            try:
                from app.services import conversation_service
                stats = await conversation_service.get_conversation_stats()
                await websocket_service.notify_dashboard_stats_update(stats)
                logger.info(f"📊 [DASHBOARD_WS] Stats update requested by user {user_id}")
            except Exception as e:
                logger.error(f"Failed to get stats for dashboard update: {str(e)}")
        
        elif message_type == "ping":
            # Respond to ping with pong
            await manager.send_personal_message({
                "type": "pong",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }, user_id)
        
        else:
            logger.warning(f"Unknown dashboard WebSocket message type: {message_type} from user {user_id}")
            
    except Exception as e:
        logger.error(f"Error handling dashboard WebSocket message from user {user_id}: {str(e)}")
        # Send error message to client
        try:
            await manager.send_personal_message({
                "type": "error",
                "message": "Internal server error",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }, user_id)
        except Exception:
            pass  # Ignore errors when sending error messages


@router.get("/status/{user_id}")
async def get_websocket_status(user_id: str):
    """
    Get WebSocket connection status for a user.
    
    Args:
        user_id: User ID to check status for
        
    Returns:
        Connection status information
    """
    try:
        is_connected = manager.is_connected(user_id)
        subscriptions = manager.get_user_subscriptions(user_id)
        
        return {
            "user_id": user_id,
            "connected": is_connected,
            "subscriptions": subscriptions,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting WebSocket status for user {user_id}: {str(e)}")
        raise handle_external_api_error("websocket", e)


@router.get("/stats")
async def get_websocket_stats():
    """
    Get WebSocket connection statistics.
    
    Returns:
        WebSocket statistics
    """
    try:
        stats = manager.get_stats()
        
        return {
            "total_connections": stats["total_connections"],
            "active_connections": stats["active_connections"],
            "total_subscriptions": stats["total_subscriptions"],
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting WebSocket stats: {str(e)}")
        raise handle_external_api_error("websocket", e)


async def calculate_unread_counts_from_database(user_id: str) -> dict:
    """
    Calculate unread message counts from the database for a user.
    
    Args:
        user_id: User ID to calculate unread counts for
        
    Returns:
        Dictionary mapping conversation_id to unread count
    """
    try:
        db = await database.get_database()
        
        # Get all conversations where the user is assigned or where there's no assigned agent
        # For assigned conversations: count unread messages
        # For unassigned conversations: count all unread messages
        pipeline = [
            {
                "$match": {
                    "$or": [
                        {"assigned_agent_id": ObjectId(user_id)},
                        {"assigned_agent_id": None}
                    ]
                }
            },
            {
                "$lookup": {
                    "from": "messages",
                    "let": {"conversation_id": "$_id"},
                    "pipeline": [
                        {
                            "$match": {
                                "$expr": {
                                    "$and": [
                                        {"$eq": ["$conversation_id", "$$conversation_id"]},
                                        {"$eq": ["$direction", "inbound"]},
                                        {"$eq": ["$status", "received"]}
                                    ]
                                }
                            }
                        },
                        {
                            "$count": "unread_count"
                        }
                    ],
                    "as": "unread_messages"
                }
            },
            {
                "$project": {
                    "conversation_id": {"$toString": "$_id"},
                    "unread_count": {
                        "$ifNull": [
                            {"$arrayElemAt": ["$unread_messages.unread_count", 0]},
                            0
                        ]
                    }
                }
            }
        ]
        
        conversations_with_unread = await db.conversations.aggregate(pipeline).to_list(None)
        
        # Convert to dictionary format
        unread_counts = {}
        for conv in conversations_with_unread:
            if conv["unread_count"] > 0:
                unread_counts[conv["conversation_id"]] = conv["unread_count"]
        
        logger.info(f"📊 [UNREAD] Calculated unread counts for user {user_id}: {unread_counts}")
        return unread_counts
        
    except Exception as e:
        logger.error(f"❌ [UNREAD] Error calculating unread counts for user {user_id}: {str(e)}")
        return {} 

@router.post("/test/status-update")
async def test_message_status_update(
    request: Request,
    current_user: User = Depends(get_current_user)
):
    """
    Test endpoint to simulate a message status update for debugging.
    """
    try:
        body = await request.json()
        conversation_id = body.get("conversation_id")
        message_id = body.get("message_id")
        status = body.get("status", "delivered")
        
        if not conversation_id or not message_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="conversation_id and message_id are required"
            )
        
        logger.info(f"🧪 [TEST] Simulating status update: {message_id} -> {status} in conversation {conversation_id}")
        
        # Send a test WebSocket notification
        await websocket_service.notify_message_status_update_optimized(
            conversation_id=conversation_id,
            message_id=message_id,
            status=status,
            message_data={
                "_id": message_id,
                "conversation_id": conversation_id,
                "status": status,
                "direction": "outbound",
                "sender_role": "agent",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
        )
        
        return {"success": True, "message": f"Status update test sent: {message_id} -> {status}"}
        
    except Exception as e:
        logger.error(f"❌ [TEST] Error in status update test: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Test failed: {str(e)}"
        ) 