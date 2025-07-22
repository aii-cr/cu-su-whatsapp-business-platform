"""
WebSocket service for real-time messaging updates.
Handles WebSocket connections and broadcasts message updates to connected clients.
"""

import json
import asyncio
from typing import Dict, Set, Optional, Any
from datetime import datetime, timezone
from fastapi import WebSocket, WebSocketDisconnect
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
    
    async def connect(self, websocket: WebSocket, user_id: str):
        """Connect a new WebSocket client."""
        await websocket.accept()
        
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
        
        # Remove from conversation subscribers
        for conversation_id, subscribers in self.conversation_subscribers.items():
            if user_id in subscribers:
                subscribers.discard(user_id)
        
        # Remove from user conversations
        if user_id in self.user_conversations:
            del self.user_conversations[user_id]
        
        logger.info(f"WebSocket disconnected for user {user_id}")
    
    async def subscribe_to_conversation(self, user_id: str, conversation_id: str):
        """Subscribe a user to a specific conversation."""
        if conversation_id not in self.conversation_subscribers:
            self.conversation_subscribers[conversation_id] = set()
        
        self.conversation_subscribers[conversation_id].add(user_id)
        
        if user_id not in self.user_conversations:
            self.user_conversations[user_id] = set()
        
        self.user_conversations[user_id].add(conversation_id)
        
        logger.info(f"User {user_id} subscribed to conversation {conversation_id}")
    
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
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_text(json.dumps(message))
                except Exception as e:
                    logger.error(f"Error sending message to user {user_id}: {str(e)}")
                    disconnected.add(connection)
            
            # Remove disconnected connections
            for connection in disconnected:
                self.active_connections[user_id].discard(connection)
    
    async def broadcast_to_conversation(self, message: dict, conversation_id: str):
        """Broadcast a message to all users subscribed to a conversation."""
        if conversation_id in self.conversation_subscribers:
            for user_id in self.conversation_subscribers[conversation_id]:
                await self.send_personal_message(message, user_id)
    
    async def broadcast_to_all(self, message: dict):
        """Broadcast a message to all connected users."""
        for user_id in list(self.active_connections.keys()):
            await self.send_personal_message(message, user_id)

# Global connection manager instance
manager = ConnectionManager()

class WebSocketService:
    """Service for handling WebSocket operations."""
    
    @staticmethod
    async def notify_new_message(conversation_id: str, message_data: dict):
        """Notify all subscribers about a new message."""
        notification = {
            "type": "new_message",
            "conversation_id": str(conversation_id),
            "message": message_data,
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

# Global WebSocket service instance
websocket_service = WebSocketService() 