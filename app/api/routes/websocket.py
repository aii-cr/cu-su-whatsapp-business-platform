"""
WebSocket routes for real-time messaging updates.
Handles WebSocket connections and subscriptions for live chat functionality.
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, status
from typing import Optional
import json
from datetime import datetime, timezone

from app.core.logger import logger
from app.services.websocket.websocket_service import manager
from app.services import websocket_service
from app.core.error_handling import handle_external_api_error

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
        await manager.connect(websocket, user_id)
        logger.info(f"WebSocket connected for user {user_id}")
        
        while True:
            # Wait for messages from the client
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Handle different message types
            await handle_websocket_message(user_id, message)
            
    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)
        logger.info(f"WebSocket disconnected for user {user_id}")
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
    try:
        message_type = message.get("type")
        
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
        # Send error message to client
        try:
            await websocket_service.send_personal_message({
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