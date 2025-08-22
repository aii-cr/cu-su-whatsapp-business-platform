"""
WebSocket service for real-time messaging updates.
Handles WebSocket connections and broadcasts message updates to connected clients.
"""

import json
import asyncio
from typing import Dict, Set, Optional, Any, List
from datetime import datetime, timezone
from fastapi import WebSocket, WebSocketDisconnect
from bson import ObjectId
from app.core.logger import logger
from app.db.models.base import PyObjectId

class ConnectionManager:
    """Manages WebSocket connections for real-time updates."""
    
    def __init__(self):
        # Store active connections by user_id
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        # Store conversation subscribers
        self.conversation_subscribers: Dict[str, Set[str]] = {}
        # Store user conversations mapping
        self.user_conversations: Dict[str, Set[str]] = {}
        # Store dashboard subscribers for real-time updates
        self.dashboard_subscribers: Set[str] = set()
        # Track unread message counts per user per conversation
        self.unread_counts: Dict[str, Dict[str, int]] = {}  # user_id -> {conversation_id: count}
    
    async def connect(self, websocket: WebSocket, user_id: str):
        """Connect a new WebSocket client."""
        # Note: websocket.accept() is now called in the route handler
        
        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()
        
        self.active_connections[user_id].add(websocket)
        logger.info(f"WebSocket connected for user {user_id}. Total connections: {len(self.active_connections[user_id])}")
    
    def disconnect(self, websocket: WebSocket, user_id: str):
        """Disconnect a WebSocket client."""
        if user_id in self.active_connections:
            self.active_connections[user_id].discard(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
                
                # Only clean up subscriptions when user has no more connections
                # Remove from conversation subscribers
                for conversation_id, subscribers in self.conversation_subscribers.items():
                    if user_id in subscribers:
                        subscribers.discard(user_id)
                
                # Remove from user conversations
                if user_id in self.user_conversations:
                    del self.user_conversations[user_id]
                
                # Remove from dashboard subscribers
                self.dashboard_subscribers.discard(user_id)
                
                # Note: Keep unread counts for when user reconnects
        
        logger.info(f"WebSocket disconnected for user {user_id}")
    
    async def subscribe_to_conversation(self, user_id: str, conversation_id: str):
        """Subscribe a user to a specific conversation."""
        logger.info(f"🔔 [WEBSOCKET] Subscription request: user {user_id} to conversation {conversation_id}")
        
        # Check if user is already subscribed
        if (conversation_id in self.conversation_subscribers and 
            user_id in self.conversation_subscribers[conversation_id]):
            logger.info(f"📋 [WEBSOCKET] User {user_id} already subscribed to conversation {conversation_id}")
            return False  # No subscription needed
        
        # Initialize conversation subscribers if needed
        if conversation_id not in self.conversation_subscribers:
            self.conversation_subscribers[conversation_id] = set()
        
        # Initialize user conversations if needed
        if user_id not in self.user_conversations:
            self.user_conversations[user_id] = set()
        
        # Add to subscription mappings
        self.conversation_subscribers[conversation_id].add(user_id)
        self.user_conversations[user_id].add(conversation_id)
        
        logger.info(f"✅ [WEBSOCKET] User {user_id} newly subscribed to conversation {conversation_id}")
        logger.info(f"📋 [WEBSOCKET] Total subscribers for conversation {conversation_id}: {len(self.conversation_subscribers[conversation_id])}")
        
        return True  # Subscription was needed and completed
    
    async def unsubscribe_from_conversation(self, user_id: str, conversation_id: str):
        """Unsubscribe a user from a specific conversation."""
        if conversation_id in self.conversation_subscribers:
            self.conversation_subscribers[conversation_id].discard(user_id)
        
        if user_id in self.user_conversations:
            self.user_conversations[user_id].discard(conversation_id)
        
        logger.info(f"User {user_id} unsubscribed from conversation {conversation_id}")
    
    async def send_personal_message(self, message: dict, user_id: str):
        """Send a message to a specific user."""
        if user_id in self.active_connections:
            disconnected = set()
            message_sent = False
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_text(json.dumps(message))
                    message_sent = True
                    logger.info(f"✅ [WEBSOCKET] Message sent to user {user_id}: {message.get('type', 'unknown')}")
                except Exception as e:
                    logger.error(f"Error sending message to user {user_id}: {str(e)}")
                    disconnected.add(connection)
            
            # Remove disconnected connections
            for connection in disconnected:
                self.active_connections[user_id].discard(connection)
            
            if not message_sent:
                logger.warning(f"⚠️ [WEBSOCKET] No active connections for user {user_id} to send message: {message.get('type', 'unknown')}")
        else:
            logger.warning(f"⚠️ [WEBSOCKET] User {user_id} not found in active connections. Available users: {list(self.active_connections.keys())}")
    
    async def broadcast_to_conversation(self, message: dict, conversation_id: str):
        """Broadcast a message to all users subscribed to a conversation."""
        logger.info(f"🔔 [WEBSOCKET] Broadcasting to conversation {conversation_id}")
        logger.info(f"🔔 [WEBSOCKET] Message type: {message.get('type', 'unknown')}")
        logger.info(f"🔔 [WEBSOCKET] Available conversation subscribers: {list(self.conversation_subscribers.keys())}")
        logger.info(f"🔔 [WEBSOCKET] Active connections: {list(self.active_connections.keys())}")
        
        if conversation_id in self.conversation_subscribers:
            subscribers = self.conversation_subscribers[conversation_id]
            logger.info(f"🔔 [WEBSOCKET] Found {len(subscribers)} subscribers for conversation {conversation_id}: {list(subscribers)}")
            
            if len(subscribers) == 0:
                logger.warning(f"⚠️ [WEBSOCKET] No active subscribers for conversation {conversation_id}")
                return
                
            for user_id in subscribers:
                logger.info(f"🔔 [WEBSOCKET] Sending message to user {user_id} for conversation {conversation_id}")
                await self.send_personal_message(message, user_id)
        else:
            logger.warning(f"❌ [WEBSOCKET] No subscribers found for conversation {conversation_id}")
            logger.info(f"📋 [WEBSOCKET] Current conversation subscribers: {dict(self.conversation_subscribers)}")
    
    async def broadcast_to_all(self, message: dict):
        """Broadcast a message to all connected users."""
        for user_id in list(self.active_connections.keys()):
            await self.send_personal_message(message, user_id)
    
    async def subscribe_to_dashboard(self, user_id: str):
        """Subscribe a user to dashboard updates."""
        self.dashboard_subscribers.add(user_id)
        # Initialize unread counts for this user if not exists
        if user_id not in self.unread_counts:
            self.unread_counts[user_id] = {}
        logger.info(f"🏠 [DASHBOARD] User {user_id} subscribed to dashboard updates")
    
    async def unsubscribe_from_dashboard(self, user_id: str):
        """Unsubscribe a user from dashboard updates."""
        self.dashboard_subscribers.discard(user_id)
        logger.info(f"🏠 [DASHBOARD] User {user_id} unsubscribed from dashboard updates")
    
    async def broadcast_to_dashboard(self, message: dict):
        """Broadcast a message to all dashboard subscribers."""
        logger.info(f"🏠 [DASHBOARD] Broadcasting to {len(self.dashboard_subscribers)} dashboard subscribers")
        logger.info(f"🏠 [DASHBOARD] Dashboard subscribers: {list(self.dashboard_subscribers)}")
        logger.info(f"🏠 [DASHBOARD] Active connections: {list(self.active_connections.keys())}")
        
        for user_id in list(self.dashboard_subscribers):
            if user_id in self.active_connections:
                logger.info(f"🏠 [DASHBOARD] Sending message to user {user_id}: {message.get('type', 'unknown')}")
                await self.send_personal_message(message, user_id)
            else:
                logger.warning(f"⚠️ [DASHBOARD] User {user_id} is subscribed but not connected")

    async def broadcast_conversation_assignment_update(self, conversation_id: str, assigned_agent_id: str, agent_name: str):
        """Broadcast conversation assignment update to all dashboard subscribers."""
        message = {
            "type": "conversation_assignment_updated",
            "conversation_id": conversation_id,
            "assigned_agent_id": assigned_agent_id,
            "agent_name": agent_name,
            "timestamp": datetime.now(datetime.UTC).isoformat()
        }
        
        logger.info(f"🔔 [WEBSOCKET] Broadcasting conversation assignment update for {conversation_id} to {len(self.dashboard_subscribers)} dashboard subscribers")
        await self.broadcast_to_dashboard(message)
    
    def increment_unread_count(self, user_id: str, conversation_id: str):
        """Increment unread message count for a user and conversation."""
        if user_id not in self.unread_counts:
            self.unread_counts[user_id] = {}
        if conversation_id not in self.unread_counts[user_id]:
            self.unread_counts[user_id][conversation_id] = 0
        self.unread_counts[user_id][conversation_id] += 1
        logger.info(f"📊 [UNREAD] User {user_id} conversation {conversation_id}: {self.unread_counts[user_id][conversation_id]} unread")
    
    def reset_unread_count(self, user_id: str, conversation_id: str):
        """Reset unread message count for a user and conversation."""
        if user_id in self.unread_counts and conversation_id in self.unread_counts[user_id]:
            self.unread_counts[user_id][conversation_id] = 0
            logger.info(f"📊 [UNREAD] Reset unread count for user {user_id} conversation {conversation_id}")
    
    def get_unread_counts(self, user_id: str) -> Dict[str, int]:
        """Get unread message counts for a user."""
        return self.unread_counts.get(user_id, {})
    
    def is_connected(self, user_id: str) -> bool:
        """Check if a user has active WebSocket connections."""
        return user_id in self.active_connections and len(self.active_connections[user_id]) > 0
    
    def get_user_subscriptions(self, user_id: str) -> list:
        """Get conversation subscriptions for a user."""
        return list(self.user_conversations.get(user_id, set()))
    
    def get_stats(self) -> dict:
        """Get WebSocket connection statistics."""
        total_connections = sum(len(connections) for connections in self.active_connections.values())
        total_subscriptions = sum(len(subs) for subs in self.conversation_subscribers.values())
        
        return {
            "total_connections": total_connections,
            "active_connections": len(self.active_connections),
            "total_subscriptions": total_subscriptions,
            "dashboard_subscribers": len(self.dashboard_subscribers)
        }

# Global connection manager instance
manager = ConnectionManager()

class WebSocketService:
    """Service for handling WebSocket operations."""
    
    @staticmethod
    async def notify_new_message(conversation_id: str, message_data: dict):
        """Notify all subscribers about a new message."""
        logger.info(f"🔔 [WEBSOCKET] notify_new_message called for conversation {conversation_id}")
        logger.info(f"🔔 [WEBSOCKET] Message data: {message_data}")
        
        # Convert ObjectId fields to strings for JSON serialization
        serialized_message = {}
        for key, value in message_data.items():
            if key == '_id':
                serialized_message[key] = str(value)
            elif key == 'conversation_id':
                serialized_message[key] = str(value)
            elif key == 'sender_id':
                serialized_message[key] = str(value) if value else None
            elif key == 'created_at' or key == 'updated_at' or key == 'read_at':
                # Handle both datetime objects and string timestamps
                if hasattr(value, 'isoformat'):
                    serialized_message[key] = value.isoformat()
                elif isinstance(value, str):
                    serialized_message[key] = value
                else:
                    serialized_message[key] = None
            elif key == 'whatsapp_data':
                # Handle nested whatsapp_data object
                if isinstance(value, dict):
                    serialized_whatsapp_data = {}
                    for w_key, w_value in value.items():
                        if isinstance(w_value, datetime):
                            serialized_whatsapp_data[w_key] = w_value.isoformat()
                        else:
                            serialized_whatsapp_data[w_key] = w_value
                    serialized_message[key] = serialized_whatsapp_data
                else:
                    serialized_message[key] = value
            elif isinstance(value, datetime):
                serialized_message[key] = value.isoformat()
            elif hasattr(value, 'isoformat'):  # Catch any other datetime-like objects
                serialized_message[key] = value.isoformat()
            else:
                serialized_message[key] = value
        
        notification = {
            "type": "new_message",
            "conversation_id": str(conversation_id),
            "message": serialized_message,
            "timestamp": datetime.now(datetime.UTC).isoformat()
        }
        
        logger.info(f"🔔 [WEBSOCKET] Sending notification: {notification}")
        
        await manager.broadcast_to_conversation(notification, str(conversation_id))
        logger.info(f"🔔 [WEBSOCKET] Broadcasted new message notification for conversation {conversation_id}")
    
    @staticmethod
    async def notify_message_status_update(conversation_id: str, message_id: str, status: str):
        """Notify about message status updates."""
        notification = {
            "type": "message_status_update",
            "conversation_id": str(conversation_id),
            "message_id": str(message_id),
            "status": status,
            "timestamp": datetime.now(datetime.UTC).isoformat()
        }
        
        await manager.broadcast_to_conversation(notification, str(conversation_id))
        logger.info(f"Broadcasted status update for message {message_id} in conversation {conversation_id}")
        
        # Invalidate Redis cache for this conversation to ensure fresh data
        try:
            from app.services.cache.redis_service import redis_service
            await redis_service.invalidate_conversation_cache(conversation_id)
            logger.info(f"🔴 [CACHE] Invalidated cache for conversation {conversation_id} after status update")
        except Exception as e:
            logger.warning(f"🔴 [CACHE] Failed to invalidate cache for conversation {conversation_id}: {str(e)}")

    @staticmethod
    async def notify_message_status_update_optimized(conversation_id: str, message_id: str, status: str, message_data: dict = None):
        """
        Optimized message status update notification that includes message data
        to avoid unnecessary cache invalidation and query refetching.
        """
        # Serialize message_data to handle ObjectId and datetime fields
        serialized_message_data = None
        if message_data:
            serialized_message_data = {}
            for key, value in message_data.items():
                if key == '_id':
                    serialized_message_data[key] = str(value)
                elif key == 'conversation_id':
                    serialized_message_data[key] = str(value)
                elif key == 'sender_id':
                    serialized_message_data[key] = str(value) if value else None
                elif key == 'reply_to_message_id':
                    serialized_message_data[key] = str(value) if value else None
                elif key == 'media_id':
                    serialized_message_data[key] = str(value) if value else None
                elif isinstance(value, datetime):
                    serialized_message_data[key] = value.isoformat()
                elif hasattr(value, 'isoformat'):
                    serialized_message_data[key] = value.isoformat()
                else:
                    serialized_message_data[key] = value
        
        notification = {
            "type": "message_status_update",
            "conversation_id": str(conversation_id),
            "message_id": str(message_id),
            "status": status,
            "message_data": serialized_message_data,  # Include serialized message data
            "timestamp": datetime.now(datetime.UTC).isoformat()
        }
        
        logger.info(f"🔔 [WEBSOCKET] Broadcasting status update notification: {notification}")
        logger.info(f"🔔 [WEBSOCKET] Message data in notification: {serialized_message_data}")
        
        await manager.broadcast_to_conversation(notification, str(conversation_id))
        logger.info(f"Broadcasted optimized status update for message {message_id} in conversation {conversation_id}")
    
    @staticmethod
    async def notify_message_read_status(
        conversation_id: str, 
        message_ids: List[str], 
        read_by_user_id: str, 
        read_by_user_name: str
    ):
        """Notify about message read status updates when inbound messages are marked as read."""
        notification = {
            "type": "messages_read",
            "conversation_id": str(conversation_id),
            "message_ids": message_ids,
            "read_by_user_id": read_by_user_id,
            "read_by_user_name": read_by_user_name,
            "timestamp": datetime.now(datetime.UTC).isoformat()
        }
        
        await manager.broadcast_to_conversation(notification, str(conversation_id))
        logger.info(f"Broadcasted read status update for {len(message_ids)} messages in conversation {conversation_id} by {read_by_user_name}")
    
    @staticmethod
    async def notify_conversation_update(conversation_id: str, update_data: dict):
        """Notify about conversation updates (status, assignment, etc.)."""
        notification = {
            "type": "conversation_update",
            "conversation_id": str(conversation_id),
            "update": update_data,
            "timestamp": datetime.now(datetime.UTC).isoformat()
        }
        
        await manager.broadcast_to_conversation(notification, str(conversation_id))
        logger.info(f"Broadcasted conversation update for {conversation_id}")
    
    @staticmethod
    async def notify_user_activity(user_id: str, activity_data: dict):
        """Notify about user activity (typing, online status, etc.)."""
        notification = {
            "type": "user_activity",
            "user_id": str(user_id),
            "activity": activity_data,
            "timestamp": datetime.now(datetime.UTC).isoformat()
        }
        
        await manager.send_personal_message(notification, str(user_id))
        logger.info(f"Sent user activity notification to {user_id}")
    
    @staticmethod
    async def notify_new_conversation(conversation_data: dict):
        """Notify all connected users about a new conversation being created."""
        # Convert ObjectId fields to strings for JSON serialization
        serialized_conversation = {}
        for key, value in conversation_data.items():
            if key == '_id':
                serialized_conversation[key] = str(value)
            elif key == 'assigned_to' or key == 'assigned_agent_id' or key == 'department_id' or key == 'created_by':
                serialized_conversation[key] = str(value) if value else None
            elif key == 'created_at' or key == 'updated_at' or key == 'last_message_at':
                # Handle both datetime objects and string timestamps
                if hasattr(value, 'isoformat'):
                    serialized_conversation[key] = value.isoformat()
                elif isinstance(value, str):
                    serialized_conversation[key] = value
                else:
                    serialized_conversation[key] = None
            elif isinstance(value, datetime):
                # Catch any other datetime objects
                serialized_conversation[key] = value.isoformat()
            elif hasattr(value, 'isoformat'):
                # Catch any other datetime-like objects
                serialized_conversation[key] = value.isoformat()
            else:
                serialized_conversation[key] = value
        
        notification = {
            "type": "new_conversation",
            "conversation": serialized_conversation,
            "timestamp": datetime.now(datetime.UTC).isoformat()
        }
        
        await manager.broadcast_to_dashboard(notification)
        logger.info(f"Broadcasted new conversation notification for conversation {conversation_data.get('_id')}")
    
    @staticmethod
    async def notify_dashboard_stats_update(stats_data: dict):
        """Notify dashboard subscribers about updated statistics."""
        notification = {
            "type": "stats_update",
            "stats": stats_data,
            "timestamp": datetime.now(datetime.UTC).isoformat()
        }
        
        await manager.broadcast_to_dashboard(notification)
        logger.info("Broadcasted dashboard stats update")
    
    @staticmethod
    async def notify_conversation_list_update(conversation_data: dict, update_type: str):
        """Notify dashboard subscribers about conversation list changes."""
        # Convert ObjectId fields to strings for JSON serialization
        serialized_conversation = {}
        for key, value in conversation_data.items():
            if key == '_id':
                serialized_conversation[key] = str(value)
            elif key == 'assigned_agent_id' or key == 'department_id' or key == 'created_by':
                serialized_conversation[key] = str(value) if value else None
            elif key == 'created_at' or key == 'updated_at' or key == 'last_message_at':
                # Handle both datetime objects and string timestamps
                if hasattr(value, 'isoformat'):
                    serialized_conversation[key] = value.isoformat()
                elif isinstance(value, str):
                    serialized_conversation[key] = value
                else:
                    serialized_conversation[key] = None
            elif isinstance(value, datetime):
                # Catch any other datetime objects
                serialized_conversation[key] = value.isoformat()
            elif hasattr(value, 'isoformat'):
                # Catch any other datetime-like objects
                serialized_conversation[key] = value.isoformat()
            else:
                serialized_conversation[key] = value
        
        notification = {
            "type": "conversation_list_update",
            "update_type": update_type,  # "created", "updated", "status_changed"
            "conversation": serialized_conversation,
            "timestamp": datetime.now(datetime.UTC).isoformat()
        }
        
        await manager.broadcast_to_dashboard(notification)
        logger.info(f"Broadcasted conversation list update: {update_type} for conversation {conversation_data.get('_id')}")
    
    @staticmethod
    async def notify_unread_count_update(user_id: str, conversation_id: str, count: int):
        """Notify a specific user about unread message count changes."""
        notification = {
            "type": "unread_count_update",
            "conversation_id": str(conversation_id),
            "unread_count": count,
            "timestamp": datetime.now(datetime.UTC).isoformat()
        }
        
        await manager.send_personal_message(notification, user_id)
        logger.info(f"Sent unread count update to user {user_id} for conversation {conversation_id}: {count}")
    
    @staticmethod
    async def notify_ai_response(conversation_id: str, message_data: dict):
        """Notify about AI-generated response."""
        # Serialize message data for JSON compatibility
        serialized_message = {}
        for key, value in message_data.items():
            if key == '_id' or key == 'conversation_id':
                serialized_message[key] = str(value)
            elif key == 'timestamp' or key == 'created_at':
                # Handle datetime serialization
                if hasattr(value, 'isoformat'):
                    serialized_message[key] = value.isoformat()
                elif isinstance(value, str):
                    serialized_message[key] = value
                else:
                    serialized_message[key] = datetime.now(datetime.UTC).isoformat()
            elif isinstance(value, datetime):
                serialized_message[key] = value.isoformat()
            elif hasattr(value, 'isoformat'):
                serialized_message[key] = value.isoformat()
            else:
                serialized_message[key] = value
        
        notification = {
            "type": "ai_response",
            "conversation_id": str(conversation_id),
            "message": serialized_message,
            "timestamp": datetime.now(datetime.UTC).isoformat()
        }
        
        await manager.broadcast_to_conversation(notification, str(conversation_id))
        logger.info(f"🤖 [WS] Broadcasted AI response notification for conversation {conversation_id}")
    
    @staticmethod
    async def notify_autoreply_toggled(conversation_id: str, enabled: bool, changed_by: str = None):
        """Notify about auto-reply toggle changes."""
        notification = {
            "type": "autoreply_toggled",
            "conversation_id": str(conversation_id),
            "ai_autoreply_enabled": enabled,
            "changed_by": changed_by,
            "timestamp": datetime.now(datetime.UTC).isoformat()
        }
        
        await manager.broadcast_to_conversation(notification, str(conversation_id))
        logger.info(f"🔔 [WS] Broadcasted auto-reply toggle notification for conversation {conversation_id}: {enabled}")

    @staticmethod
    async def notify_ai_processing_started(conversation_id: str, message_id: str):
        """Notify that AI agent has started processing a message."""
        notification = {
            "type": "ai_processing_started",
            "conversation_id": str(conversation_id),
            "message_id": str(message_id),
            "timestamp": datetime.now(datetime.UTC).isoformat()
        }
        
        await manager.broadcast_to_conversation(notification, str(conversation_id))
        logger.info(f"🤖 [WS] Notified AI processing started for conversation {conversation_id}")

    @staticmethod
    async def notify_ai_agent_activity(conversation_id: str, activity_type: str, activity_description: str, metadata: dict = None):
        """Notify about AI agent activity during processing (e.g., using RAG, tools, etc.)."""
        notification = {
            "type": "ai_agent_activity",
            "conversation_id": str(conversation_id),
            "activity_type": activity_type,  # e.g., "rag_search", "tool_execution", "intent_detection"
            "activity_description": activity_description,  # e.g., "Using internal knowledge", "Detecting intent"
            "metadata": metadata or {},
            "timestamp": datetime.now(datetime.UTC).isoformat()
        }
        
        await manager.broadcast_to_conversation(notification, str(conversation_id))
        logger.info(f"🤖 [WS] Notified AI agent activity for conversation {conversation_id}: {activity_type} - {activity_description}")

    @staticmethod
    async def notify_ai_processing_completed(conversation_id: str, message_id: str, success: bool, response_sent: bool):
        """Notify that AI agent has completed processing a message."""
        notification = {
            "type": "ai_processing_completed",
            "conversation_id": str(conversation_id),
            "message_id": str(message_id),
            "success": success,
            "response_sent": response_sent,
            "timestamp": datetime.now(datetime.UTC).isoformat()
        }
        
        await manager.broadcast_to_conversation(notification, str(conversation_id))
        logger.info(f"🤖 [WS] Notified AI processing completed for conversation {conversation_id}: success={success}, response_sent={response_sent}")
    
    @staticmethod
    async def reset_unread_count_for_user(user_id: str, conversation_id: str):
        """Reset unread count when user reads messages."""
        manager.reset_unread_count(user_id, conversation_id)
        await WebSocketService.notify_unread_count_update(user_id, conversation_id, 0)

    @staticmethod
    async def handle_conversation_assignment_change(conversation_id: str, new_assigned_agent_id: str = None):
        """
        Handle unread count updates when conversation assignment changes.
        This ensures unread counts are properly recalculated when conversations are claimed or reassigned.
        """
        try:
            from app.db.client import database
            db = await database.get_database()
            
            # Calculate the correct unread count from database
            unread_count = await db.messages.count_documents({
                "conversation_id": ObjectId(conversation_id),
                "direction": "inbound",
                "status": "received"
            })
            
            # Clear unread counts for all dashboard subscribers for this conversation
            for user_id in list(manager.dashboard_subscribers):
                if user_id in manager.unread_counts and conversation_id in manager.unread_counts[user_id]:
                    # Only clear if this user is not the new assigned agent
                    if new_assigned_agent_id is None or user_id != new_assigned_agent_id:
                        manager.unread_counts[user_id][conversation_id] = 0
                        await WebSocketService.notify_unread_count_update(user_id, conversation_id, 0)
                        logger.info(f"📊 [UNREAD] Cleared unread count for user {user_id} after assignment change")
            
            # Set unread count for the new assigned agent if there are unread messages
            if new_assigned_agent_id and unread_count > 0:
                if new_assigned_agent_id not in manager.unread_counts:
                    manager.unread_counts[new_assigned_agent_id] = {}
                manager.unread_counts[new_assigned_agent_id][conversation_id] = unread_count
                await WebSocketService.notify_unread_count_update(new_assigned_agent_id, conversation_id, unread_count)
                logger.info(f"📊 [UNREAD] Set unread count for newly assigned agent {new_assigned_agent_id}: {unread_count}")
            
            logger.info(f"📊 [UNREAD] Handled assignment change for conversation {conversation_id}, unread count: {unread_count}")
            
        except Exception as e:
            logger.error(f"❌ [UNREAD] Error handling conversation assignment change: {str(e)}")

    @staticmethod
    async def notify_incoming_message_processed(
        conversation_id: str, 
        message: dict, 
        is_new_conversation: bool = False,
        conversation: dict = None
    ):
        """
        Handle all notifications for an incoming message processing.
        This centralizes all WebSocket notifications for incoming messages.
        """
        try:
            # 1. Always notify about the new message to conversation subscribers
            await WebSocketService.notify_new_message(conversation_id, message)
            
            # 2. Invalidate Redis cache for this conversation
            try:
                from app.services.whatsapp.message.cursor_message_service import cursor_message_service
                await cursor_message_service.invalidate_conversation_cache(conversation_id)
                logger.info(f"🔴 [CACHE] Invalidated cache for conversation {conversation_id} after new message")
            except Exception as cache_error:
                logger.warning(f"🔴 [CACHE] Failed to invalidate cache for conversation {conversation_id}: {str(cache_error)}")
            
            # 3. Update unread counts - always calculate from database for accuracy
            try:
                from app.db.client import database
                db = await database.get_database()
                
                # Get conversation to find assigned agent
                conversation = await db.conversations.find_one({"_id": ObjectId(conversation_id)})
                
                # Calculate the correct unread count from database
                unread_count = await db.messages.count_documents({
                    "conversation_id": ObjectId(conversation_id),
                    "direction": "inbound",
                    "status": "received"
                })
                
                if conversation and conversation.get("assigned_agent_id"):
                    assigned_agent_id = str(conversation["assigned_agent_id"])
                    active_viewers = manager.conversation_subscribers.get(conversation_id, set())
                    
                    # Only update unread count for assigned agent if they're not currently viewing
                    if assigned_agent_id not in active_viewers:
                        # Set the unread count directly from database calculation
                        if assigned_agent_id not in manager.unread_counts:
                            manager.unread_counts[assigned_agent_id] = {}
                        manager.unread_counts[assigned_agent_id][conversation_id] = unread_count
                        
                        await WebSocketService.notify_unread_count_update(assigned_agent_id, conversation_id, unread_count)
                        logger.info(f"📊 [UNREAD] Set unread count for assigned agent {assigned_agent_id}: {unread_count}")
                    else:
                        logger.info(f"📊 [UNREAD] Assigned agent {assigned_agent_id} is currently viewing conversation, not updating unread count")
                        
                        # If agent is viewing, auto-mark the message as read
                        try:
                            from app.db.models.whatsapp.chat.message import MessageStatus
                            from datetime import datetime, timezone
                            
                            # Update the message status to read
                            result = await db.messages.update_one(
                                {"_id": ObjectId(message["_id"])},
                                {
                                    "$set": {
                                        "status": MessageStatus.READ,
                                        "read_at": datetime.now(datetime.UTC),
                                        "updated_at": datetime.now(datetime.UTC)
                                    }
                                }
                            )
                            
                            if result.modified_count > 0:
                                logger.info(f"📖 [AUTO_READ] Auto-marked message {message['_id']} as read for viewing agent {assigned_agent_id}")
                                
                                # Notify about the read status update
                                await WebSocketService.notify_message_read_status(
                                    conversation_id,
                                    message_ids=[str(message["_id"])],
                                    read_by_user_id=assigned_agent_id,
                                    read_by_user_name="Agent"
                                )
                                
                                # Reset unread count since message was auto-read
                                manager.unread_counts[assigned_agent_id][conversation_id] = 0
                                await WebSocketService.notify_unread_count_update(assigned_agent_id, conversation_id, 0)
                        except Exception as auto_read_error:
                            logger.error(f"❌ [AUTO_READ] Error auto-marking message as read: {str(auto_read_error)}")
                else:
                    logger.info(f"📊 [UNREAD] No assigned agent found for conversation {conversation_id}")
                    # For unassigned conversations, update unread count for all dashboard subscribers
                    for user_id in list(manager.dashboard_subscribers):
                        if user_id in manager.active_connections:
                            # Set the unread count directly from database calculation
                            if user_id not in manager.unread_counts:
                                manager.unread_counts[user_id] = {}
                            manager.unread_counts[user_id][conversation_id] = unread_count
                            
                            await WebSocketService.notify_unread_count_update(user_id, conversation_id, unread_count)
                            logger.info(f"📊 [UNREAD] Set unread count for dashboard subscriber {user_id}: {unread_count}")
            except Exception as e:
                logger.error(f"❌ [UNREAD] Error updating unread count: {str(e)}")
            
            # 4. If this is a new conversation, notify dashboard subscribers
            if is_new_conversation and conversation:
                logger.info(f"🆕 [CONVERSATION] Broadcasting new conversation creation for {conversation_id}")
                await WebSocketService.notify_new_conversation(conversation)
                await WebSocketService.notify_conversation_list_update(conversation, "created")
            
            # 5. If conversation status was updated, notify dashboard
            if conversation and conversation.get("status") == "waiting":
                await WebSocketService.notify_conversation_list_update(conversation, "status_changed")
            
            # 6. Update dashboard stats
            try:
                from app.services import conversation_service
                stats = await conversation_service.get_conversation_stats()
                await WebSocketService.notify_dashboard_stats_update(stats)
            except Exception as e:
                logger.error(f"Failed to update dashboard stats: {str(e)}")
            
            logger.info(f"✅ [WEBSOCKET] All notifications sent for incoming message in conversation {conversation_id}")
            
        except Exception as e:
            logger.error(f"❌ [WEBSOCKET] Error in notify_incoming_message_processed: {str(e)}")
            # Don't re-raise to avoid breaking the webhook processing

# Global WebSocket service instance
websocket_service = WebSocketService() 