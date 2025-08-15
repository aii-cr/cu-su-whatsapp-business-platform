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
        logger.info(f"🔔 [WEBSOCKET] Available conversation subscribers: {list(self.conversation_subscribers.keys())}")
        logger.info(f"🔔 [WEBSOCKET] Active connections: {list(self.active_connections.keys())}")
        
        if conversation_id in self.conversation_subscribers:
            subscribers = self.conversation_subscribers[conversation_id]
            logger.info(f"🔔 [WEBSOCKET] Found {len(subscribers)} subscribers for conversation {conversation_id}: {list(subscribers)}")
            for user_id in subscribers:
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
            "timestamp": datetime.now(timezone.utc).isoformat()
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
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        await manager.broadcast_to_conversation(notification, str(conversation_id))
        logger.info(f"Broadcasted new message notification for conversation {conversation_id}")
    
    @staticmethod
    async def notify_message_status_update(conversation_id: str, message_id: str, status: str):
        """Notify about message status updates."""
        notification = {
            "type": "message_status_update",
            "conversation_id": str(conversation_id),
            "message_id": str(message_id),
            "status": status,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        await manager.broadcast_to_conversation(notification, str(conversation_id))
        logger.info(f"Broadcasted status update for message {message_id} in conversation {conversation_id}")
    
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
            "timestamp": datetime.now(timezone.utc).isoformat()
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
            "timestamp": datetime.now(timezone.utc).isoformat()
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
            "timestamp": datetime.now(timezone.utc).isoformat()
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
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        await manager.broadcast_to_dashboard(notification)
        logger.info(f"Broadcasted new conversation notification for conversation {conversation_data.get('_id')}")
    
    @staticmethod
    async def notify_dashboard_stats_update(stats_data: dict):
        """Notify dashboard subscribers about updated statistics."""
        notification = {
            "type": "stats_update",
            "stats": stats_data,
            "timestamp": datetime.now(timezone.utc).isoformat()
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
            "timestamp": datetime.now(timezone.utc).isoformat()
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
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        await manager.send_personal_message(notification, user_id)
        logger.info(f"Sent unread count update to user {user_id} for conversation {conversation_id}: {count}")
    
    @staticmethod
    async def reset_unread_count_for_user(user_id: str, conversation_id: str):
        """Reset unread count when user reads messages."""
        manager.reset_unread_count(user_id, conversation_id)
        await WebSocketService.notify_unread_count_update(user_id, conversation_id, 0)

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
            
            # 2. Update unread counts for the assigned agent only
            try:
                from app.db.client import database
                db = await database.get_database()
                
                # Get conversation to find assigned agent
                conversation = await db.conversations.find_one({"_id": ObjectId(conversation_id)})
                if conversation and conversation.get("assigned_agent_id"):
                    assigned_agent_id = str(conversation["assigned_agent_id"])
                    active_viewers = manager.conversation_subscribers.get(conversation_id, set())
                    
                    # Only increment unread count for assigned agent if they're not currently viewing
                    if assigned_agent_id not in active_viewers:
                        manager.increment_unread_count(assigned_agent_id, conversation_id)
                        # Notify about unread count update
                        unread_count = manager.unread_counts.get(assigned_agent_id, {}).get(conversation_id, 0)
                        await WebSocketService.notify_unread_count_update(assigned_agent_id, conversation_id, unread_count)
                        logger.info(f"📊 [UNREAD] Incremented unread count for assigned agent {assigned_agent_id}: {unread_count}")
                    else:
                        logger.info(f"📊 [UNREAD] Assigned agent {assigned_agent_id} is currently viewing conversation, not incrementing unread count")
                        
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
                                        "read_at": datetime.now(timezone.utc),
                                        "updated_at": datetime.now(timezone.utc)
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
                        except Exception as auto_read_error:
                            logger.error(f"❌ [AUTO_READ] Error auto-marking message as read: {str(auto_read_error)}")
                else:
                    logger.info(f"📊 [UNREAD] No assigned agent found for conversation {conversation_id}")
                    # For unassigned conversations, we should still track unread counts
                    # but we need to determine which agents should be notified
                    # For now, let's increment unread count for all dashboard subscribers
                    # This is a simplified approach - in a real system, you might want to
                    # notify specific agents based on department, availability, etc.
                    
                    # Get all dashboard subscribers and increment their unread count
                    for user_id in list(manager.dashboard_subscribers):
                        if user_id in manager.active_connections:
                            manager.increment_unread_count(user_id, conversation_id)
                            unread_count = manager.unread_counts.get(user_id, {}).get(conversation_id, 0)
                            await WebSocketService.notify_unread_count_update(user_id, conversation_id, unread_count)
                            logger.info(f"📊 [UNREAD] Incremented unread count for dashboard subscriber {user_id}: {unread_count}")
            except Exception as e:
                logger.error(f"❌ [UNREAD] Error updating unread count: {str(e)}")
            
            # 3. If this is a new conversation, notify dashboard subscribers
            if is_new_conversation and conversation:
                logger.info(f"🆕 [CONVERSATION] Broadcasting new conversation creation for {conversation_id}")
                await WebSocketService.notify_new_conversation(conversation)
                await WebSocketService.notify_conversation_list_update(conversation, "created")
            
            # 4. If conversation status was updated, notify dashboard
            if conversation and conversation.get("status") == "waiting":
                await WebSocketService.notify_conversation_list_update(conversation, "status_changed")
            
            # 5. Update dashboard stats
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