"""
Test unread messages banner functionality.
Tests the complete flow of unread messages, banner display, and automatic marking as read.
"""

import pytest
from datetime import datetime, timezone
from bson import ObjectId
from app.core.config import settings
from app.services.websocket.websocket_service import websocket_service, manager


@pytest.mark.asyncio
class TestUnreadMessagesBanner:
    """Test unread messages banner functionality."""

    @pytest.fixture
    def test_user_data(self):
        """Test user data."""
        return {
            "_id": "507f1f77bcf86cd799439011",
            "first_name": "Test",
            "last_name": "Agent",
            "email": "agent@example.com",
            "password": "testpassword123",
            "role_ids": ["role1"],
            "permissions": ["conversation:read", "conversation:write"],
            "is_active": True,
            "is_verified": True,
            "department_id": "dept1",
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z"
        }
    
    @pytest.fixture
    def test_conversation_data(self):
        """Test conversation data."""
        return {
            "_id": "507f1f77bcf86cd799439012",
            "customer_phone": "50684716592",
            "customer_name": "Steve Arce",
            "assigned_agent_id": "507f1f77bcf86cd799439011",
            "assigned_department_id": "dept1",
            "status": "active",
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z"
        }

    @pytest.fixture
    async def test_conversation_with_messages(self, test_user_data, test_conversation_data):
        """Create a test conversation with unread inbound messages."""
        from app.db.client import database
        
        db = await database._get_db()
        
        # Create conversation assigned to test user
        conversation_data = {
            **test_conversation_data,
            "assigned_agent_id": ObjectId(test_user_data["_id"]),
            "status": "active",
            "unread_count": 0
        }
        
        conversation_result = await db.conversations.insert_one(conversation_data)
        conversation_id = conversation_result.inserted_id
        
        # Create unread inbound messages
        unread_messages = [
            {
                "conversation_id": conversation_id,
                "direction": "inbound",
                "sender_role": "customer",
                "sender_phone": "+1234567890",
                "sender_name": "Test Customer",
                "text_content": "Hello, I need help",
                "status": "delivered",
                "timestamp": datetime.now(timezone.utc),
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc),
                "type": "text"
            },
            {
                "conversation_id": conversation_id,
                "direction": "inbound",
                "sender_role": "customer",
                "sender_phone": "+1234567890",
                "sender_name": "Test Customer",
                "text_content": "Can you assist me?",
                "status": "delivered",
                "timestamp": datetime.now(timezone.utc),
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc),
                "type": "text"
            }
        ]
        
        await db.messages.insert_many(unread_messages)
        
        yield {
            "conversation_id": str(conversation_id),
            "user_id": test_user_data["_id"],
            "messages": unread_messages
        }
        
        # Cleanup
        await db.conversations.delete_one({"_id": conversation_id})
        await db.messages.delete_many({"conversation_id": conversation_id})

    async def test_unread_count_calculation(self, test_conversation_with_messages):
        """Test that unread count is calculated correctly."""
        from app.services.whatsapp.message.message_service import message_service
        
        conversation_id = test_conversation_with_messages["conversation_id"]
        
        # Get messages for conversation
        messages_data = await message_service.get_conversation_messages(conversation_id)
        
        # Count unread inbound messages
        unread_count = 0
        for message in messages_data["messages"]:
            if (message["direction"] == "inbound" and 
                message["status"] != "read" and 
                message["sender_role"] == "customer"):
                unread_count += 1
        
        assert unread_count == 2, f"Expected 2 unread messages, got {unread_count}"

    async def test_mark_messages_as_read_websocket(self, test_conversation_with_messages):
        """Test marking messages as read via WebSocket."""
        from app.api.routes.websocket import handle_mark_messages_read
        
        conversation_id = test_conversation_with_messages["conversation_id"]
        user_id = test_conversation_with_messages["user_id"]
        
        # Mark messages as read
        await handle_mark_messages_read(user_id, conversation_id)
        
        # Verify messages are marked as read
        from app.db.client import database
        db = await database._get_db()
        
        unread_messages = await db.messages.find({
            "conversation_id": ObjectId(conversation_id),
            "direction": "inbound",
            "status": {"$in": ["received", "delivered"]}
        }).to_list(length=None)
        
        assert len(unread_messages) == 0, "All messages should be marked as read"
        
        # Verify read messages exist
        read_messages = await db.messages.find({
            "conversation_id": ObjectId(conversation_id),
            "direction": "inbound",
            "status": "read"
        }).to_list(length=None)
        
        assert len(read_messages) == 2, "Should have 2 read messages"

    async def test_mark_messages_as_read_http(self, async_client, test_user_data, test_conversation_with_messages):
        """Test marking messages as read via HTTP endpoint."""
        from app.schemas.whatsapp.chat.message import MessageReadRequest
        
        conversation_id = test_conversation_with_messages["conversation_id"]
        
        # Login
        login_response = await async_client.post(
            f"{settings.API_PREFIX}/auth/login",
            json={
                "email": test_user_data["email"],
                "password": test_user_data["password"]
            }
        )
        assert login_response.status_code == 200
        
        # Mark messages as read
        request_data = MessageReadRequest(conversation_id=conversation_id)
        
        response = await async_client.post(
            f"{settings.API_PREFIX}/whatsapp/chat/messages/mark-read",
            json=request_data.model_dump()
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["messages_marked_read"] == 2
        assert data["conversation_id"] == conversation_id

    async def test_only_assigned_agent_can_mark_as_read(self, async_client, test_user_data, test_conversation_with_messages):
        """Test that only the assigned agent can mark messages as read."""
        from app.schemas.whatsapp.chat.message import MessageReadRequest
        
        conversation_id = test_conversation_with_messages["conversation_id"]
        
        # Create another user
        other_user_data = {
            "email": "other@example.com",
            "password": "testpassword123",
            "first_name": "Other",
            "last_name": "User",
            "role": "agent"
        }
        
        # Register other user
        register_response = await async_client.post(
            f"{settings.API_PREFIX}/auth/register",
            json=other_user_data
        )
        assert register_response.status_code == 201
        
        # Login as other user
        login_response = await async_client.post(
            f"{settings.API_PREFIX}/auth/login",
            json={
                "email": other_user_data["email"],
                "password": other_user_data["password"]
            }
        )
        assert login_response.status_code == 200
        
        # Try to mark messages as read (should fail)
        request_data = MessageReadRequest(conversation_id=conversation_id)
        
        response = await async_client.post(
            f"{settings.API_PREFIX}/whatsapp/chat/messages/mark-read",
            json=request_data.model_dump()
        )
        
        assert response.status_code == 403
        assert "Only the assigned agent can mark messages as read" in response.json()["detail"]

    async def test_websocket_unread_count_updates(self, test_conversation_with_messages):
        """Test WebSocket unread count updates."""
        conversation_id = test_conversation_with_messages["conversation_id"]
        user_id = test_conversation_with_messages["user_id"]
        
        # Simulate user subscribing to conversation
        await manager.subscribe_to_conversation(user_id, conversation_id)
        
        # Simulate incoming message
        new_message = {
            "conversation_id": conversation_id,
            "direction": "inbound",
            "sender_role": "customer",
            "sender_phone": "+1234567890",
            "sender_name": "Test Customer",
            "text_content": "Another message",
            "status": "delivered",
            "timestamp": datetime.now(timezone.utc),
            "type": "text"
        }
        
        # Process incoming message
        await websocket_service.notify_incoming_message_processed(
            conversation_id,
            new_message,
            is_new_conversation=False
        )
        
        # Check if unread count was incremented for assigned agent
        unread_count = manager.get_unread_counts(user_id).get(conversation_id, 0)
        assert unread_count > 0, "Unread count should be incremented for assigned agent"

    async def test_unread_banner_disappears_after_marking_read(self, test_conversation_with_messages):
        """Test that unread banner disappears after marking messages as read."""
        from app.api.routes.websocket import handle_mark_messages_read
        
        conversation_id = test_conversation_with_messages["conversation_id"]
        user_id = test_conversation_with_messages["user_id"]
        
        # Initially should have unread messages
        from app.db.client import database
        db = await database._get_db()
        
        unread_messages = await db.messages.find({
            "conversation_id": ObjectId(conversation_id),
            "direction": "inbound",
            "status": {"$in": ["received", "delivered"]}
        }).to_list(length=None)
        
        assert len(unread_messages) == 2, "Should have 2 unread messages initially"
        
        # Mark messages as read
        await handle_mark_messages_read(user_id, conversation_id)
        
        # Verify no unread messages remain
        unread_messages_after = await db.messages.find({
            "conversation_id": ObjectId(conversation_id),
            "direction": "inbound",
            "status": {"$in": ["received", "delivered"]}
        }).to_list(length=None)
        
        assert len(unread_messages_after) == 0, "Should have no unread messages after marking as read"

    async def test_websocket_message_read_confirmation(self, test_conversation_with_messages):
        """Test WebSocket message read confirmation."""
        from app.api.routes.websocket import handle_mark_messages_read
        
        conversation_id = test_conversation_with_messages["conversation_id"]
        user_id = test_conversation_with_messages["user_id"]
        
        # Subscribe user to WebSocket
        await manager.subscribe_to_conversation(user_id, conversation_id)
        
        # Mark messages as read
        await handle_mark_messages_read(user_id, conversation_id)
        
        # The confirmation message should be sent to the user
        # This is handled by the WebSocket service internally
        # We can verify by checking that the unread count is reset
        unread_count = manager.get_unread_counts(user_id).get(conversation_id, 0)
        assert unread_count == 0, "Unread count should be reset after marking as read"

    async def test_conversation_without_assigned_agent(self, test_conversation_data):
        """Test behavior when conversation has no assigned agent."""
        from app.db.client import database
        
        db = await database._get_db()
        
        # Create conversation without assigned agent
        conversation_data = {
            **test_conversation_data,
            "assigned_agent_id": None,
            "status": "pending"
        }
        
        conversation_result = await db.conversations.insert_one(conversation_data)
        conversation_id = conversation_result.inserted_id
        
        # Create unread message
        message_data = {
            "conversation_id": conversation_id,
            "direction": "inbound",
            "sender_role": "customer",
            "sender_phone": "+1234567890",
            "sender_name": "Test Customer",
            "text_content": "Hello",
            "status": "delivered",
            "timestamp": datetime.now(timezone.utc),
            "type": "text"
        }
        
        await db.messages.insert_one(message_data)
        
        # Process incoming message - should not increment unread count for anyone
        await websocket_service.notify_incoming_message_processed(
            str(conversation_id),
            message_data,
            is_new_conversation=False
        )
        
        # Verify no unread counts were incremented
        all_unread_counts = manager.unread_counts
        assert len(all_unread_counts) == 0, "No unread counts should be incremented for unassigned conversation"
        
        # Cleanup
        await db.conversations.delete_one({"_id": conversation_id})
        await db.messages.delete_many({"conversation_id": conversation_id})
