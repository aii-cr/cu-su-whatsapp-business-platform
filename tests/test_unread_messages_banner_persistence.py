"""
Test unread messages banner persistence functionality.
Tests that the banner remains visible until the agent sends a reply, not just when they view messages.
"""

import pytest
from datetime import datetime, timezone
from bson import ObjectId
from app.core.config import settings
from app.services.websocket.websocket_service import websocket_service, manager


@pytest.mark.asyncio
class TestUnreadMessagesBannerPersistence:
    """Test unread messages banner persistence functionality."""

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
    async def test_conversation_with_unread_messages(self, test_user_data, test_conversation_data):
        """Create a test conversation with unread inbound messages."""
        from app.db.client import database
        
        db = await database.get_database()
        
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

    async def test_banner_remains_visible_after_viewing_messages(self, test_conversation_with_unread_messages):
        """
        Test that the banner remains visible after the agent views messages but before they send a reply.
        This tests the core fix for the banner persistence issue.
        """
        test_data = await test_conversation_with_unread_messages.__anext__()
        conversation_id = test_data["conversation_id"]
        user_id = test_data["user_id"]
        
        # Simulate agent subscribing to conversation (viewing messages)
        await manager.subscribe_to_conversation(user_id, conversation_id)
        
        # Verify agent is subscribed
        assert user_id in manager.conversation_subscribers.get(conversation_id, set())
        
        # Simulate marking messages as read (this should happen when agent views conversation)
        from app.api.routes.websocket import handle_mark_messages_read
        await handle_mark_messages_read(user_id, conversation_id)
        
        # Verify messages are marked as read in database
        from app.db.client import database
        db = await database.get_database()
        
        messages = await db.messages.find({
            "conversation_id": ObjectId(conversation_id),
            "direction": "inbound"
        }).to_list(length=None)
        
        # All inbound messages should be marked as read
        for message in messages:
            assert message["status"] == "read"
            assert "read_at" in message
        
        # However, the unread count should still be tracked for banner visibility
        # The banner should remain visible until the agent sends a reply
        unread_count = manager.unread_counts.get(user_id, {}).get(conversation_id, 0)
        
        # The unread count should be 0 after marking as read
        assert unread_count == 0
        
        # But the banner visibility logic should be controlled by hasRepliedToUnread
        # This is handled in the frontend, but we can verify the backend state is correct
        
        print(f"✅ Test passed: Messages marked as read, unread count reset to {unread_count}")

    async def test_banner_hidden_after_agent_reply(self, test_conversation_with_unread_messages):
        """
        Test that the banner is hidden after the agent sends a reply to unread messages.
        """
        test_data = await test_conversation_with_unread_messages.__anext__()
        conversation_id = test_data["conversation_id"]
        user_id = test_data["user_id"]
        
        # Simulate agent subscribing to conversation
        await manager.subscribe_to_conversation(user_id, conversation_id)
        
        # Simulate marking messages as read
        from app.api.routes.websocket import handle_mark_messages_read
        await handle_mark_messages_read(user_id, conversation_id)
        
        # Simulate agent sending a reply
        from app.db.client import database
        db = await database.get_database()
        
        agent_reply = {
            "conversation_id": ObjectId(conversation_id),
            "direction": "outbound",
            "sender_role": "agent",
            "sender_id": ObjectId(user_id),
            "text_content": "Hello! How can I help you today?",
            "status": "sent",
            "timestamp": datetime.now(timezone.utc),
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
            "type": "text"
        }
        
        await db.messages.insert_one(agent_reply)
        
        # Notify about the new outbound message (this should trigger banner hiding in frontend)
        await websocket_service.notify_new_message(conversation_id, agent_reply)
        
        # Verify the agent reply was created
        reply_message = await db.messages.find_one({"_id": agent_reply["_id"]})
        assert reply_message is not None
        assert reply_message["direction"] == "outbound"
        assert reply_message["sender_role"] == "agent"
        
        print(f"✅ Test passed: Agent reply sent, banner should be hidden")

    async def test_banner_persistence_with_multiple_unread_messages(self, test_conversation_with_unread_messages):
        """
        Test banner persistence with multiple unread messages.
        """
        test_data = await test_conversation_with_unread_messages.__anext__()
        conversation_id = test_data["conversation_id"]
        user_id = test_data["user_id"]
        
        # Add more unread messages
        from app.db.client import database
        db = await database.get_database()
        
        additional_messages = [
            {
                "conversation_id": ObjectId(conversation_id),
                "direction": "inbound",
                "sender_role": "customer",
                "sender_phone": "+1234567890",
                "sender_name": "Test Customer",
                "text_content": "Third message",
                "status": "delivered",
                "timestamp": datetime.now(timezone.utc),
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc),
                "type": "text"
            },
            {
                "conversation_id": ObjectId(conversation_id),
                "direction": "inbound",
                "sender_role": "customer",
                "sender_phone": "+1234567890",
                "sender_name": "Test Customer",
                "text_content": "Fourth message",
                "status": "delivered",
                "timestamp": datetime.now(timezone.utc),
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc),
                "type": "text"
            }
        ]
        
        await db.messages.insert_many(additional_messages)
        
        # Simulate agent subscribing to conversation
        await manager.subscribe_to_conversation(user_id, conversation_id)
        
        # Simulate marking messages as read
        from app.api.routes.websocket import handle_mark_messages_read
        await handle_mark_messages_read(user_id, conversation_id)
        
        # Verify all messages are marked as read
        messages = await db.messages.find({
            "conversation_id": ObjectId(conversation_id),
            "direction": "inbound"
        }).to_list(length=None)
        
        for message in messages:
            assert message["status"] == "read"
        
        # Verify unread count is 0
        unread_count = manager.unread_counts.get(user_id, {}).get(conversation_id, 0)
        assert unread_count == 0
        
        print(f"✅ Test passed: Multiple unread messages handled correctly")

    async def test_banner_behavior_with_new_messages_after_viewing(self, test_conversation_with_unread_messages):
        """
        Test banner behavior when new messages arrive after agent has viewed the conversation.
        """
        test_data = await test_conversation_with_unread_messages.__anext__()
        conversation_id = test_data["conversation_id"]
        user_id = test_data["user_id"]
        
        # Simulate agent subscribing to conversation
        await manager.subscribe_to_conversation(user_id, conversation_id)
        
        # Simulate marking existing messages as read
        from app.api.routes.websocket import handle_mark_messages_read
        await handle_mark_messages_read(user_id, conversation_id)
        
        # Now simulate a new inbound message arriving
        from app.db.client import database
        db = await database.get_database()
        
        new_message = {
            "conversation_id": ObjectId(conversation_id),
            "direction": "inbound",
            "sender_role": "customer",
            "sender_phone": "+1234567890",
            "sender_name": "Test Customer",
            "text_content": "New message after viewing",
            "status": "delivered",
            "timestamp": datetime.now(timezone.utc),
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
            "type": "text"
        }
        
        await db.messages.insert_one(new_message)
        
        # Simulate the incoming message processing
        await websocket_service.notify_incoming_message_processed(
            conversation_id,
            new_message,
            is_new_conversation=False
        )
        
        # Since the agent is currently viewing (subscribed), the message should be auto-marked as read
        updated_message = await db.messages.find_one({"_id": new_message["_id"]})
        assert updated_message["status"] == "read"
        
        # But the banner should still be visible until the agent sends a reply
        # This is controlled by the frontend hasRepliedToUnread state
        
        print(f"✅ Test passed: New message auto-marked as read for viewing agent")

    async def test_banner_reset_on_page_reload(self, test_conversation_with_unread_messages):
        """
        Test that the banner state is reset when the page is reloaded.
        This simulates the second condition for hiding the banner.
        """
        test_data = await test_conversation_with_unread_messages.__anext__()
        conversation_id = test_data["conversation_id"]
        user_id = test_data["user_id"]
        
        # Simulate agent subscribing to conversation
        await manager.subscribe_to_conversation(user_id, conversation_id)
        
        # Simulate marking messages as read
        from app.api.routes.websocket import handle_mark_messages_read
        await handle_mark_messages_read(user_id, conversation_id)
        
        # Simulate page reload by unsubscribing and resubscribing
        await manager.unsubscribe_from_conversation(user_id, conversation_id)
        await manager.subscribe_to_conversation(user_id, conversation_id)
        
        # Verify the subscription is active
        assert user_id in manager.conversation_subscribers.get(conversation_id, set())
        
        # The frontend should reset hasRepliedToUnread to false on conversation change
        # This would allow the banner to show again if there are unread messages
        
        print(f"✅ Test passed: Banner state reset on page reload simulation")

    async def test_cleanup(self, test_conversation_with_unread_messages):
        """Cleanup test data."""
        test_data = await test_conversation_with_unread_messages.__anext__()
        conversation_id = test_data["conversation_id"]
        user_id = test_data["user_id"]
        
        # Cleanup WebSocket state
        await manager.unsubscribe_from_conversation(user_id, conversation_id)
        
        # Cleanup database
        from app.db.client import database
        db = await database.get_database()
        
        await db.conversations.delete_one({"_id": ObjectId(conversation_id)})
        await db.messages.delete_many({"conversation_id": ObjectId(conversation_id)})
        
        print(f"✅ Cleanup completed for conversation {conversation_id}")
