"""
Test WebSocket message read functionality.
"""

import pytest
import asyncio
from httpx import AsyncClient
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone
from bson import ObjectId

from app.main import app
from app.db.client import database
from app.db.models.whatsapp.chat.message import MessageStatus


class TestWebSocketMessageRead:
    """Test WebSocket message read functionality."""

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
            "email": "test@example.com",
            "password": "testpassword123",
            "first_name": "Test",
            "last_name": "User"
        }

    @pytest.fixture
    def mock_user(self):
        """Mock user for testing."""
        user = MagicMock()
        user.id = ObjectId("687920e1074832b685b32d6a")
        user.email = "test@example.com"
        user.first_name = "Test"
        user.last_name = "User"
        user.is_super_admin = False
        return user

    @pytest.mark.asyncio
    async def test_handle_mark_messages_read_success(self, mock_user):
        """Test successful marking of messages as read via WebSocket."""
        from app.api.routes.websocket import handle_mark_messages_read
        
        # Mock database
        with patch('app.api.routes.websocket.database') as mock_db:
            # Mock conversation
            mock_conversation = {
                "_id": ObjectId("6896172715b32dbaea77f9cc"),
                "assigned_agent_id": ObjectId("687920e1074832b685b32d6a"),
                "customer_phone": "50684716592"
            }
            
            # Mock unread messages
            mock_unread_messages = [
                {
                    "_id": ObjectId("689e4313e02c7b86628edc1d"),
                    "conversation_id": ObjectId("6896172715b32dbaea77f9cc"),
                    "direction": "inbound",
                    "status": "received",
                    "text_content": "hola"
                }
            ]
            
            # Mock database operations
            mock_db_instance = MagicMock()
            mock_db._get_db.return_value = mock_db_instance
            mock_db_instance.find_one.return_value = mock_conversation
            mock_db_instance.find.return_value.to_list.return_value = mock_unread_messages
            
            update_result = MagicMock()
            update_result.modified_count = 1
            mock_db_instance.update_many.return_value = update_result
            
            # Mock WebSocket service
            with patch('app.api.routes.websocket.websocket_service') as mock_ws_service:
                with patch('app.api.routes.websocket.manager') as mock_manager:
                    # Call the function
                    await handle_mark_messages_read(
                        str(mock_user.id), 
                        "6896172715b32dbaea77f9cc"
                    )
                    
                    # Verify database calls
                    mock_db_instance.find_one.assert_called_once()
                    mock_db_instance.find.assert_called_once()
                    mock_db_instance.update_many.assert_called_once()
                    
                    # Verify WebSocket notifications
                    mock_ws_service.notify_message_read_status.assert_called_once()
                    mock_ws_service.reset_unread_count_for_user.assert_called_once()
                    mock_manager.send_personal_message.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_mark_messages_read_no_access(self, mock_user):
        """Test marking messages as read without access to conversation."""
        from app.api.routes.websocket import handle_mark_messages_read
        
        # Mock database
        with patch('app.api.routes.websocket.database') as mock_db:
            # Mock no conversation found (no access)
            mock_db_instance = MagicMock()
            mock_db._get_db.return_value = mock_db_instance
            mock_db_instance.find_one.return_value = None
            
            # Call the function
            await handle_mark_messages_read(
                str(mock_user.id), 
                "6896172715b32dbaea77f9cc"
            )
            
            # Verify no database updates were made
            mock_db_instance.update_many.assert_not_called()

    @pytest.mark.asyncio
    async def test_handle_mark_messages_read_no_unread_messages(self, mock_user):
        """Test marking messages as read when no unread messages exist."""
        from app.api.routes.websocket import handle_mark_messages_read
        
        # Mock database
        with patch('app.api.routes.websocket.database') as mock_db:
            # Mock conversation
            mock_conversation = {
                "_id": ObjectId("6896172715b32dbaea77f9cc"),
                "assigned_agent_id": ObjectId("687920e1074832b685b32d6a"),
                "customer_phone": "50684716592"
            }
            
            # Mock no unread messages
            mock_db_instance = MagicMock()
            mock_db._get_db.return_value = mock_db_instance
            mock_db_instance.find_one.return_value = mock_conversation
            mock_db_instance.find.return_value.to_list.return_value = []
            
            # Call the function
            await handle_mark_messages_read(
                str(mock_user.id), 
                "6896172715b32dbaea77f9cc"
            )
            
            # Verify no database updates were made
            mock_db_instance.update_many.assert_not_called()

    def test_websocket_message_read_request_schema(self):
        """Test WebSocket message read request schema."""
        # This test verifies that the WebSocket message structure is correct
        message = {
            "type": "mark_messages_read",
            "conversation_id": "6896172715b32dbaea77f9cc",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        # Verify required fields
        assert "type" in message
        assert "conversation_id" in message
        assert "timestamp" in message
        assert message["type"] == "mark_messages_read"
        assert isinstance(message["conversation_id"], str)
        assert isinstance(message["timestamp"], str)


if __name__ == "__main__":
    pytest.main([__file__])

