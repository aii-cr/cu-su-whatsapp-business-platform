"""
Test message read status functionality.
"""

import pytest
import asyncio
from httpx import AsyncClient
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone

from app.main import app
from app.core.config import settings
from app.db.models.whatsapp.chat.message import Message, MessageStatus, MessageDirection, SenderRole
from app.schemas.whatsapp.chat.message import MessageReadRequest, MessageReadResponse

class TestMessageReadStatus:
    """Test message read status functionality."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    @pytest.fixture
    def async_client(self):
        """Create async test client."""
        return AsyncClient(base_url="http://test")
    
    @pytest.fixture
    def test_user_data(self):
        """Test user data."""
        return {
            "_id": "507f1f77bcf86cd799439011",
            "first_name": "Test",
            "last_name": "Agent",
            "email": "agent@example.com",
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
    def test_messages_data(self):
        """Test messages data."""
        return [
            {
                "_id": "507f1f77bcf86cd799439013",
                "conversation_id": "507f1f77bcf86cd799439012",
                "direction": "inbound",
                "sender_role": "customer",
                "sender_phone": "50684716592",
                "message_type": "text",
                "text_content": "Hello",
                "status": "received",
                "timestamp": "2024-01-01T10:00:00Z",
                "created_at": "2024-01-01T10:00:00Z",
                "updated_at": "2024-01-01T10:00:00Z"
            },
            {
                "_id": "507f1f77bcf86cd799439014",
                "conversation_id": "507f1f77bcf86cd799439012",
                "direction": "inbound",
                "sender_role": "customer",
                "sender_phone": "50684716592",
                "message_type": "text",
                "text_content": "How are you?",
                "status": "delivered",
                "timestamp": "2024-01-01T10:01:00Z",
                "created_at": "2024-01-01T10:01:00Z",
                "updated_at": "2024-01-01T10:01:00Z"
            },
            {
                "_id": "507f1f77bcf86cd799439015",
                "conversation_id": "507f1f77bcf86cd799439012",
                "direction": "outbound",
                "sender_role": "agent",
                "sender_id": "507f1f77bcf86cd799439011",
                "message_type": "text",
                "text_content": "I'm good, thanks!",
                "status": "read",
                "timestamp": "2024-01-01T10:02:00Z",
                "created_at": "2024-01-01T10:02:00Z",
                "updated_at": "2024-01-01T10:02:00Z"
            }
        ]
    
    @pytest.mark.asyncio
    async def test_mark_messages_read_success(self, async_client, test_user_data, test_conversation_data, test_messages_data):
        """Test successful marking of messages as read."""
        with patch('app.services.auth.utils.session_auth.get_current_user') as mock_get_user, \
             patch('app.db.client.database._get_db') as mock_get_db, \
             patch('app.services.websocket.websocket_service.websocket_service.notify_message_read_status') as mock_notify:
            
            # Mock current user
            mock_user = MagicMock()
            mock_user.id = test_user_data["_id"]
            mock_user.email = test_user_data["email"]
            mock_user.first_name = test_user_data["first_name"]
            mock_user.last_name = test_user_data["last_name"]
            mock_get_user.return_value = mock_user
            
            # Mock database
            mock_db = MagicMock()
            mock_get_db.return_value = mock_db
            
            # Mock conversation lookup
            mock_db.conversations.find_one.return_value = test_conversation_data
            
            # Mock unread messages lookup
            unread_messages = [msg for msg in test_messages_data if msg["direction"] == "inbound" and msg["status"] in ["received", "delivered"]]
            mock_db.messages.find.return_value.to_list.return_value = unread_messages
            
            # Mock update result
            mock_update_result = MagicMock()
            mock_update_result.modified_count = len(unread_messages)
            mock_db.messages.update_many.return_value = mock_update_result
            
            # Test mark messages as read request
            request_data = {
                "conversation_id": test_conversation_data["_id"]
            }
            
            response = await async_client.post(
                f"{settings.API_PREFIX}/whatsapp/chat/messages/mark-read",
                json=request_data,
                cookies={"session_token": "test_token"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["conversation_id"] == test_conversation_data["_id"]
            assert data["messages_marked_read"] == len(unread_messages)
            assert "timestamp" in data
            
            # Verify database calls
            mock_db.conversations.find_one.assert_called_once()
            mock_db.messages.find.assert_called_once()
            mock_db.messages.update_many.assert_called_once()
            
            # Verify WebSocket notification
            mock_notify.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_mark_messages_read_no_access(self, async_client, test_user_data):
        """Test marking messages as read without access to conversation."""
        with patch('app.services.auth.utils.session_auth.get_current_user') as mock_get_user, \
             patch('app.db.client.database._get_db') as mock_get_db:
            
            # Mock current user
            mock_user = MagicMock()
            mock_user.id = test_user_data["_id"]
            mock_user.email = test_user_data["email"]
            mock_get_user.return_value = mock_user
            
            # Mock database
            mock_db = MagicMock()
            mock_get_db.return_value = mock_db
            
            # Mock conversation lookup - user doesn't have access
            mock_db.conversations.find_one.return_value = None
            
            # Test mark messages as read request
            request_data = {
                "conversation_id": "507f1f77bcf86cd799439012"
            }
            
            response = await async_client.post(
                f"{settings.API_PREFIX}/whatsapp/chat/messages/mark-read",
                json=request_data,
                cookies={"session_token": "test_token"}
            )
            
            assert response.status_code == 403
    
    @pytest.mark.asyncio
    async def test_mark_messages_read_no_unread_messages(self, async_client, test_user_data, test_conversation_data):
        """Test marking messages as read when no unread messages exist."""
        with patch('app.services.auth.utils.session_auth.get_current_user') as mock_get_user, \
             patch('app.db.client.database._get_db') as mock_get_db:
            
            # Mock current user
            mock_user = MagicMock()
            mock_user.id = test_user_data["_id"]
            mock_user.email = test_user_data["email"]
            mock_get_user.return_value = mock_user
            
            # Mock database
            mock_db = MagicMock()
            mock_get_db.return_value = mock_db
            
            # Mock conversation lookup
            mock_db.conversations.find_one.return_value = test_conversation_data
            
            # Mock unread messages lookup - no unread messages
            mock_db.messages.find.return_value.to_list.return_value = []
            
            # Test mark messages as read request
            request_data = {
                "conversation_id": test_conversation_data["_id"]
            }
            
            response = await async_client.post(
                f"{settings.API_PREFIX}/whatsapp/chat/messages/mark-read",
                json=request_data,
                cookies={"session_token": "test_token"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["conversation_id"] == test_conversation_data["_id"]
            assert data["messages_marked_read"] == 0
    
    def test_message_read_request_schema(self):
        """Test MessageReadRequest schema validation."""
        # Valid request
        valid_request = MessageReadRequest(conversation_id="507f1f77bcf86cd799439012")
        assert valid_request.conversation_id == "507f1f77bcf86cd799439012"
        
        # Invalid request - missing conversation_id
        with pytest.raises(ValueError):
            MessageReadRequest()
    
    def test_message_read_response_schema(self):
        """Test MessageReadResponse schema validation."""
        now = datetime.now(timezone.utc)
        response = MessageReadResponse(
            conversation_id="507f1f77bcf86cd799439012",
            messages_marked_read=2,
            timestamp=now
        )
        
        assert response.conversation_id == "507f1f77bcf86cd799439012"
        assert response.messages_marked_read == 2
        assert response.timestamp == now


if __name__ == "__main__":
    pytest.main([__file__])

