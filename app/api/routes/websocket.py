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
        
        # Send current unread counts to user
        unread_counts = manager.get_unread_counts(user_id)
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


async def handle_dashboard_websocket_message(user_id: str, message: dict):
    """
    Handle incoming WebSocket messages from dashboard clients.
    
    Args:
        user_id: User ID sending the message
        message: Message data from client
    """
    try:
        message_type = message.get("type")
        
        if message_type == "mark_conversation_read":
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