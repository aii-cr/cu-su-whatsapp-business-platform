"""
Test unread messages functionality.
Tests WebSocket connection, message marking as read, and unread count updates.
"""

import pytest
import asyncio
from datetime import datetime, timezone
from bson import ObjectId
from fastapi.testclient import TestClient
from app.main import app
from app.db.client import database
from app.services.websocket.websocket_service import manager, websocket_service
from app.services.whatsapp.message.message_service import message_service
from app.services import conversation_service
from app.services.auth.utils.session_auth import create_session_token

client = TestClient(app)

@pytest.fixture
async def test_user():
    """Create a test user for authentication."""
    db = await database.get_database()
    
    # Create test user
    user_data = {
        "email": "test@example.com",
        "password": "testpassword123",
        "first_name": "Test",
        "last_name": "User",
        "role": "agent",
        "is_active": True,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc)
    }
    
    result = await db.users.insert_one(user_data)
    user_id = result.inserted_id
    
    # Create session token
    session_token = create_session_token({
        "_id": user_id,
        "email": user_data["email"]
    })
    
    yield {
        "id": str(user_id),
        "email": user_data["email"],
        "session_token": session_token
    }
    
    # Cleanup
    await db.users.delete_one({"_id": user_id})

@pytest.fixture
async def test_conversation(test_user):
    """Create a test conversation."""
    db = await database.get_database()
    
    # Create test conversation
    conversation_data = {
        "customer_phone": "+1234567890",
        "customer_name": "Test Customer",
        "assigned_agent_id": ObjectId(test_user["id"]),
        "status": "active",
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc)
    }
    
    result = await db.conversations.insert_one(conversation_data)
    conversation_id = result.inserted_id
    
    yield str(conversation_id)
    
    # Cleanup
    await db.conversations.delete_one({"_id": conversation_id})
    await db.messages.delete_many({"conversation_id": conversation_id})

@pytest.fixture
async def test_messages(test_conversation):
    """Create test messages for the conversation."""
    db = await database.get_database()
    
    # Create inbound messages (unread)
    inbound_messages = []
    for i in range(3):
        message_data = {
            "conversation_id": ObjectId(test_conversation),
            "type": "text",
            "direction": "inbound",
            "sender_role": "customer",
            "sender_phone": "+1234567890",
            "sender_name": "Test Customer",
            "text_content": f"Test message {i+1}",
            "status": "received",
            "timestamp": datetime.now(timezone.utc),
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }
        
        result = await db.messages.insert_one(message_data)
        inbound_messages.append(str(result.inserted_id))
    
    # Create outbound message (read)
    outbound_message_data = {
        "conversation_id": ObjectId(test_conversation),
        "type": "text",
        "direction": "outbound",
        "sender_role": "agent",
        "sender_id": ObjectId("507f1f77bcf86cd799439011"),  # Dummy agent ID
        "text_content": "Agent response",
        "status": "read",
        "timestamp": datetime.now(timezone.utc),
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc)
    }
    
    result = await db.messages.insert_one(outbound_message_data)
    
    yield {
        "conversation_id": test_conversation,
        "inbound_messages": inbound_messages,
        "outbound_message": str(result.inserted_id)
    }

class TestUnreadMessages:
    """Test unread messages functionality."""
    
    @pytest.mark.asyncio
    async def test_websocket_connection(self, test_user):
        """Test WebSocket connection establishment."""
        # Test WebSocket status endpoint
        headers = {"Cookie": f"session_token={test_user['session_token']}"}
        response = client.get(f"/ws/status/{test_user['id']}", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "connected" in data
        assert "subscriptions" in data
    
    @pytest.mark.asyncio
    async def test_unread_count_calculation(self, test_user, test_conversation, test_messages):
        """Test unread message count calculation."""
        db = await database.get_database()
        
        # Get unread messages count
        unread_count = await db.messages.count_documents({
            "conversation_id": ObjectId(test_conversation),
            "direction": "inbound",
            "status": {"$in": ["received", "delivered"]}
        })
        
        assert unread_count == 3  # Should have 3 unread inbound messages
    
    @pytest.mark.asyncio
    async def test_mark_messages_as_read(self, test_user, test_conversation, test_messages):
        """Test marking messages as read via WebSocket."""
        db = await database.get_database()
        
        # Verify initial state
        unread_count = await db.messages.count_documents({
            "conversation_id": ObjectId(test_conversation),
            "direction": "inbound",
            "status": {"$in": ["received", "delivered"]}
        })
        assert unread_count == 3
        
        # Mark messages as read
        result = await db.messages.update_many(
            {
                "conversation_id": ObjectId(test_conversation),
                "direction": "inbound",
                "status": {"$in": ["received", "delivered"]}
            },
            {
                "$set": {
                    "status": "read",
                    "read_at": datetime.now(timezone.utc),
                    "updated_at": datetime.now(timezone.utc)
                }
            }
        )
        
        assert result.modified_count == 3
        
        # Verify final state
        unread_count = await db.messages.count_documents({
            "conversation_id": ObjectId(test_conversation),
            "direction": "inbound",
            "status": {"$in": ["received", "delivered"]}
        })
        assert unread_count == 0
    
    @pytest.mark.asyncio
    async def test_websocket_manager_unread_counts(self, test_user, test_conversation):
        """Test WebSocket manager unread count tracking."""
        user_id = test_user["id"]
        
        # Test initial state
        unread_counts = manager.get_unread_counts(user_id)
        assert test_conversation not in unread_counts or unread_counts[test_conversation] == 0
        
        # Increment unread count
        manager.increment_unread_count(user_id, test_conversation)
        unread_counts = manager.get_unread_counts(user_id)
        assert unread_counts[test_conversation] == 1
        
        # Reset unread count
        manager.reset_unread_count(user_id, test_conversation)
        unread_counts = manager.get_unread_counts(user_id)
        assert unread_counts[test_conversation] == 0
    
    @pytest.mark.asyncio
    async def test_conversation_subscription(self, test_user, test_conversation):
        """Test conversation subscription functionality."""
        user_id = test_user["id"]
        
        # Subscribe to conversation
        subscription_needed = await manager.subscribe_to_conversation(user_id, test_conversation)
        assert subscription_needed == True
        
        # Check subscription
        subscriptions = manager.get_user_subscriptions(user_id)
        assert test_conversation in subscriptions
        
        # Unsubscribe from conversation
        await manager.unsubscribe_from_conversation(user_id, test_conversation)
        subscriptions = manager.get_user_subscriptions(user_id)
        assert test_conversation not in subscriptions

class TestMessageService:
    """Test message service functionality."""
    
    @pytest.mark.asyncio
    async def test_create_inbound_message(self, test_conversation):
        """Test creating an inbound message."""
        message_data = await message_service.create_message(
            conversation_id=test_conversation,
            message_type="text",
            direction="inbound",
            sender_role="customer",
            sender_phone="+1234567890",
            sender_name="Test Customer",
            text_content="Test inbound message",
            status="received"
        )
        
        assert message_data is not None
        assert message_data["direction"] == "inbound"
        assert message_data["sender_role"] == "customer"
        assert message_data["status"] == "received"
    
    @pytest.mark.asyncio
    async def test_update_message_status(self, test_conversation):
        """Test updating message status."""
        # Create a message first
        message_data = await message_service.create_message(
            conversation_id=test_conversation,
            message_type="text",
            direction="inbound",
            sender_role="customer",
            sender_phone="+1234567890",
            sender_name="Test Customer",
            text_content="Test message for status update",
            status="received"
        )
        
        message_id = str(message_data["_id"])
        
        # Update status to read
        success = await message_service.update_message_status(
            message_id=message_id,
            status="read"
        )
        
        assert success == True
        
        # Verify the update
        updated_message = await message_service.get_message(message_id)
        assert updated_message["status"] == "read"
        assert "read_at" in updated_message

class TestWebSocketNotifications:
    """Test WebSocket notification functionality."""
    
    @pytest.mark.asyncio
    async def test_new_message_notification(self, test_conversation):
        """Test new message notification."""
        # Create a test message
        message_data = await message_service.create_message(
            conversation_id=test_conversation,
            message_type="text",
            direction="inbound",
            sender_role="customer",
            sender_phone="+1234567890",
            sender_name="Test Customer",
            text_content="Test notification message",
            status="received"
        )
        
        # Test notification (this would normally be called by the webhook handler)
        await websocket_service.notify_new_message(test_conversation, message_data)
        
        # The notification should be sent to conversation subscribers
        # In a real test, we would need to set up a WebSocket client to receive the notification
    
    @pytest.mark.asyncio
    async def test_message_read_notification(self, test_conversation, test_user):
        """Test message read notification."""
        # Create a test message
        message_data = await message_service.create_message(
            conversation_id=test_conversation,
            message_type="text",
            direction="inbound",
            sender_role="customer",
            sender_phone="+1234567890",
            sender_name="Test Customer",
            text_content="Test read notification message",
            status="received"
        )
        
        message_id = str(message_data["_id"])
        
        # Test read notification
        await websocket_service.notify_message_read_status(
            conversation_id=test_conversation,
            message_ids=[message_id],
            read_by_user_id=test_user["id"],
            read_by_user_name="Test Agent"
        )
        
        # The notification should be sent to conversation subscribers
        # In a real test, we would need to set up a WebSocket client to receive the notification

if __name__ == "__main__":
    pytest.main([__file__])
