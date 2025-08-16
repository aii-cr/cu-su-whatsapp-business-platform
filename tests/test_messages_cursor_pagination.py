"""Tests for cursor-based message pagination functionality."""

import pytest
from datetime import datetime, timezone
from bson import ObjectId
from unittest.mock import AsyncMock, patch

from app.services.whatsapp.message.cursor_message_service import cursor_message_service
from app.services.cache.redis_service import redis_service


class TestCursorMessageService:
    """Test cases for cursor-based message pagination."""
    
    @pytest.fixture
    def mock_db(self):
        """Mock database for testing."""
        with patch('app.services.whatsapp.message.cursor_message_service.cursor_message_service._get_db') as mock:
            db = AsyncMock()
            # Mock the messages collection with proper method chaining
            messages_collection = AsyncMock()
            # Mock the find method to return an object with sort and limit methods
            find_mock = AsyncMock()
            sort_mock = AsyncMock()
            limit_mock = AsyncMock()
            find_mock.sort.return_value = sort_mock
            sort_mock.limit.return_value = limit_mock
            messages_collection.find.return_value = find_mock
            db.messages = messages_collection
            mock.return_value = db
            yield db
    
    @pytest.fixture
    def mock_redis(self):
        """Mock Redis for testing."""
        with patch('app.services.whatsapp.message.cursor_message_service.redis_service') as mock:
            # Create AsyncMock for Redis service methods
            mock.get_cached_message_window = AsyncMock()
            mock.cache_message_window = AsyncMock()
            mock.invalidate_conversation_cache = AsyncMock()
            yield mock
    
    @pytest.fixture
    def sample_messages(self):
        """Sample messages for testing."""
        return [
            {
                "_id": ObjectId("507f1f77bcf86cd799439011"),
                "conversation_id": ObjectId("507f1f77bcf86cd799439012"),
                "text_content": "Message 1",
                "timestamp": datetime.now(timezone.utc),
                "direction": "inbound",
                "sender_role": "customer"
            },
            {
                "_id": ObjectId("507f1f77bcf86cd799439013"),
                "conversation_id": ObjectId("507f1f77bcf86cd799439012"),
                "text_content": "Message 2",
                "timestamp": datetime.now(timezone.utc),
                "direction": "outbound",
                "sender_role": "agent"
            },
            {
                "_id": ObjectId("507f1f77bcf86cd799439014"),
                "conversation_id": ObjectId("507f1f77bcf86cd799439012"),
                "text_content": "Message 3",
                "timestamp": datetime.now(timezone.utc),
                "direction": "inbound",
                "sender_role": "customer"
            }
        ]
    
    @pytest.mark.asyncio
    async def test_get_messages_cursor_no_before(self, mock_db, mock_redis, sample_messages):
        """Test getting latest messages without cursor."""
        # Mock Redis cache miss
        mock_redis.get_cached_message_window.return_value = None
        
        # Mock database query
        mock_cursor = AsyncMock()
        mock_cursor.to_list.return_value = sample_messages[:2]  # Return 2 messages
        mock_db.messages.find.return_value.sort.return_value.limit.return_value.to_list.return_value = sample_messages[:2]
        
        # Test
        result = await cursor_message_service.get_messages_cursor(
            conversation_id="507f1f77bcf86cd799439012",
            limit=2
        )
        
        # Assertions
        assert len(result["messages"]) == 2
        assert result["has_more"] is False
        assert result["next_cursor"] is None
        assert result["cache_hit"] is False
        
        # Verify database query
        mock_db.messages.find.assert_called_once_with({
            "conversation_id": ObjectId("507f1f77bcf86cd799439012")
        })
    
    @pytest.mark.asyncio
    async def test_get_messages_cursor_with_before(self, mock_db, sample_messages):
        """Test getting messages with cursor pagination."""
        # Mock database query
        mock_cursor = AsyncMock()
        mock_cursor.to_list.return_value = sample_messages[1:3]  # Return 2 messages
        mock_db.messages.find.return_value.sort.return_value.limit.return_value.to_list.return_value = sample_messages[1:3]
        
        # Test
        result = await cursor_message_service.get_messages_cursor(
            conversation_id="507f1f77bcf86cd799439012",
            limit=2,
            before="507f1f77bcf86cd799439011"
        )
        
        # Assertions
        assert len(result["messages"]) == 2
        assert result["has_more"] is False
        assert result["next_cursor"] == "507f1f77bcf86cd799439013"
        assert result["cache_hit"] is False
        
        # Verify database query with cursor filter
        mock_db.messages.find.assert_called_once_with({
            "conversation_id": ObjectId("507f1f77bcf86cd799439012"),
            "_id": {"$lt": ObjectId("507f1f77bcf86cd799439011")}
        })
    
    @pytest.mark.asyncio
    async def test_get_messages_cursor_with_cache_hit(self, mock_db, mock_redis, sample_messages):
        """Test getting messages from cache."""
        # Mock Redis cache hit
        cached_data = {
            "messages": [
                {
                    "_id": "507f1f77bcf86cd799439011",
                    "conversation_id": "507f1f77bcf86cd799439012",
                    "text_content": "Message 1",
                    "direction": "inbound",
                    "sender_role": "customer"
                }
            ],
            "next_cursor": None,
            "has_more": False,
            "etag": "abc123"
        }
        mock_redis.get_cached_message_window.return_value = cached_data
        
        # Test
        result = await cursor_message_service.get_messages_cursor(
            conversation_id="507f1f77bcf86cd799439012",
            limit=2
        )
        
        # Assertions
        assert len(result["messages"]) == 1
        assert result["has_more"] is False
        assert result["next_cursor"] is None
        assert result["cache_hit"] is True
        assert result["etag"] == "abc123"
        
        # Verify cache was checked
        mock_redis.get_cached_message_window.assert_called_once()
        # Verify database was not queried
        mock_db.messages.find.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_get_messages_cursor_has_more(self, mock_db, sample_messages):
        """Test getting messages when there are more available."""
        # Mock database query with extra message
        mock_cursor = AsyncMock()
        mock_cursor.to_list.return_value = sample_messages  # Return 3 messages for limit 2
        mock_db.messages.find.return_value.sort.return_value.limit.return_value.to_list.return_value = sample_messages
        
        # Test
        result = await cursor_message_service.get_messages_cursor(
            conversation_id="507f1f77bcf86cd799439012",
            limit=2
        )
        
        # Assertions
        assert len(result["messages"]) == 2  # Should only return limit
        assert result["has_more"] is True
        assert result["next_cursor"] == "507f1f77bcf86cd799439013"
    
    @pytest.mark.asyncio
    async def test_get_messages_around(self, mock_db, sample_messages):
        """Test getting messages around a specific message."""
        # Mock anchor message exists
        mock_db.messages.find_one.return_value = sample_messages[1]
        
        # Mock before and after queries
        mock_before_cursor = AsyncMock()
        mock_before_cursor.to_list.return_value = [sample_messages[0]]
        mock_after_cursor = AsyncMock()
        mock_after_cursor.to_list.return_value = [sample_messages[1], sample_messages[2]]
        
        # Create separate find mocks for before and after
        find_mock1 = AsyncMock()
        sort_mock1 = AsyncMock()
        limit_mock1 = AsyncMock()
        find_mock1.sort.return_value = sort_mock1
        sort_mock1.limit.return_value = limit_mock1
        limit_mock1.to_list.return_value = [sample_messages[0]]
        
        find_mock2 = AsyncMock()
        sort_mock2 = AsyncMock()
        limit_mock2 = AsyncMock()
        find_mock2.sort.return_value = sort_mock2
        sort_mock2.limit.return_value = limit_mock2
        limit_mock2.to_list.return_value = [sample_messages[1], sample_messages[2]]
        
        mock_db.messages.find.side_effect = [find_mock1, find_mock2]
        
        # Test
        result = await cursor_message_service.get_messages_around(
            conversation_id="507f1f77bcf86cd799439012",
            anchor_id="507f1f77bcf86cd799439013",
            limit=3
        )
        
        # Assertions
        assert len(result["messages"]) == 3
        assert result["has_more"] is False
        assert result["cache_hit"] is False
        
        # Verify anchor message was checked
        mock_db.messages.find_one.assert_called_once_with({
            "_id": ObjectId("507f1f77bcf86cd799439013"),
            "conversation_id": ObjectId("507f1f77bcf86cd799439012")
        })
    
    @pytest.mark.asyncio
    async def test_get_messages_around_anchor_not_found(self, mock_db):
        """Test getting messages around non-existent anchor."""
        # Mock anchor message not found
        mock_db.messages.find_one.return_value = None
        
        # Test should raise ValueError
        with pytest.raises(ValueError, match="Anchor message.*not found"):
            await cursor_message_service.get_messages_around(
                conversation_id="507f1f77bcf86cd799439012",
                anchor_id="507f1f77bcf86cd799439013",
                limit=3
            )
    
    @pytest.mark.asyncio
    async def test_invalidate_conversation_cache(self, mock_redis):
        """Test invalidating conversation cache."""
        # Test
        await cursor_message_service.invalidate_conversation_cache("507f1f77bcf86cd799439012")
        
        # Verify cache invalidation was called
        mock_redis.invalidate_conversation_cache.assert_called_once_with("507f1f77bcf86cd799439012")
    



class TestCursorMessageServiceIntegration:
    """Integration tests for cursor-based message pagination."""
    
    @pytest.mark.asyncio
    async def test_full_pagination_flow(self, mock_db, mock_redis, sample_messages):
        """Test complete pagination flow with cache."""
        # First request - cache miss, should cache result
        mock_redis.get_cached_message_window.return_value = None
        mock_cursor = AsyncMock()
        mock_cursor.to_list.return_value = sample_messages[:2]
        mock_db.messages.find.return_value.sort.return_value.limit.return_value.to_list.return_value = sample_messages[:2]
        
        result1 = await cursor_message_service.get_messages_cursor(
            conversation_id="507f1f77bcf86cd799439012",
            limit=2
        )
        
        assert len(result1["messages"]) == 2
        assert result1["cache_hit"] is False
        
        # Verify cache was set
        mock_redis.cache_message_window.assert_called_once()
        
        # Second request - should hit cache
        cached_data = {
            "messages": result1["messages"],
            "next_cursor": result1["next_cursor"],
            "has_more": result1["has_more"],
            "etag": "abc123"
        }
        mock_redis.get_cached_message_window.return_value = cached_data
        
        result2 = await cursor_message_service.get_messages_cursor(
            conversation_id="507f1f77bcf86cd799439012",
            limit=2
        )
        
        assert result2["cache_hit"] is True
        assert len(result2["messages"]) == 2
