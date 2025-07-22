"""
WebSocket routes for real-time messaging updates.
Handles WebSocket connections and subscriptions for live chat functionality.
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from typing import Optional
import json
from datetime import datetime, timezone

from app.core.logger import logger
from app.services.websocket.websocket_service import manager, websocket_service
from app.db.client import database

router = APIRouter(prefix="/ws", tags=["WebSocket"])

@router.websocket("/chat/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    """
    WebSocket endpoint for real-time chat updates.
    
    Args:
        websocket: WebSocket connection
        user_id: User ID for the connection
    """
    await manager.connect(websocket, user_id)
    
    try:
        while True:
            # Wait for messages from the client
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Handle different message types
            await handle_websocket_message(user_id, message)
            
    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)
    except Exception as e:
        logger.error(f"WebSocket error for user {user_id}: {str(e)}")
        manager.disconnect(websocket, user_id)
        

async def handle_websocket_message(user_id: str, message: dict):
    """
    Handle incoming WebSocket messages from clients.
    
    Args:
        user_id: User ID sending the message
        message: Message data from client
    """
    message_type = message.get("type")
    
    try:
        if message_type == "subscribe_conversation":
            conversation_id = message.get("conversation_id")
            if conversation_id:
                await manager.subscribe_to_conversation(user_id, conversation_id)
                await websocket_service.send_personal_message({
                    "type": "subscription_confirmed",
                    "conversation_id": conversation_id,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }, user_id)
        
        elif message_type == "unsubscribe_conversation":
            conversation_id = message.get("conversation_id")
            if conversation_id:
                await manager.unsubscribe_from_conversation(user_id, conversation_id)
                await websocket_service.send_personal_message({
                    "type": "unsubscription_confirmed",
                    "conversation_id": conversation_id,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }, user_id)
        
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
        
        elif message_type == "ping":
            # Respond to ping with pong
            await websocket_service.send_personal_message({
                "type": "pong",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }, user_id)
        
        else:
            logger.warning(f"Unknown WebSocket message type: {message_type} from user {user_id}")
    
    except Exception as e:
        logger.error(f"Error handling WebSocket message from user {user_id}: {str(e)}")
        await websocket_service.send_personal_message({
            "type": "error",
            "message": "Internal server error",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }, user_id)

@router.get("/status/{user_id}")
async def get_websocket_status(user_id: str):
    """
    Get WebSocket connection status for a user.
    
    Args:
        user_id: User ID to check status for
    
    Returns:
        Connection status information
    """
    is_connected = user_id in manager.active_connections
    connection_count = len(manager.active_connections.get(user_id, set()))
    subscribed_conversations = list(manager.user_conversations.get(user_id, set()))
    
    return {
        "user_id": user_id,
        "connected": is_connected,
        "connection_count": connection_count,
        "subscribed_conversations": subscribed_conversations,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

@router.get("/stats")
async def get_websocket_stats():
    """
    Get WebSocket connection statistics.
    
    Returns:
        WebSocket statistics
    """
    total_users = len(manager.active_connections)
    total_connections = sum(len(connections) for connections in manager.active_connections.values())
    total_conversations = len(manager.conversation_subscribers)
    
    return {
        "total_users": total_users,
        "total_connections": total_connections,
        "total_conversations": total_conversations,
        "timestamp": datetime.now(timezone.utc).isoformat()
    } 