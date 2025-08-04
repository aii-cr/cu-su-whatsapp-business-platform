"""
Unit tests for the audit service.
Tests all audit logging functionality with proper mocking.
"""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from bson import ObjectId

from app.services.audit.audit_service import AuditService


class TestAuditService:
    """Test cases for AuditService."""

    @pytest.fixture
    def mock_database(self):
        """Mock database fixture."""
        with patch("app.services.audit.audit_service.database") as mock_db:
            mock_db.db.audit_logs = AsyncMock()
            yield mock_db

    @pytest.fixture
    def mock_logger(self):
        """Mock logger fixture."""
        with patch("app.services.audit.audit_service.logger") as mock_log:
            yield mock_log

    @pytest.mark.asyncio
    async def test_log_event_success(self, mock_database, mock_logger):
        """Test successful audit event logging."""
        # Setup
        mock_result = MagicMock()
        mock_result.inserted_id = ObjectId()
        mock_database.db.audit_logs.insert_one.return_value = mock_result

        # Execute
        result = await AuditService.log_event(
            action="test_action",
            actor_id="507f1f77bcf86cd799439011",
            actor_name="Test User",
            customer_phone="+1234567890",
            conversation_id="507f1f77bcf86cd799439012",
            department_id="507f1f77bcf86cd799439013",
            payload={"test": "data"},
            metadata={"context": "test"},
            correlation_id="test-correlation-id",
        )

        # Verify
        assert result == str(mock_result.inserted_id)
        mock_database.db.audit_logs.insert_one.assert_called_once()

        # Verify the inserted document structure
        call_args = mock_database.db.audit_logs.insert_one.call_args[0][0]
        assert call_args["action"] == "test_action"
        assert call_args["actor_id"] == ObjectId("507f1f77bcf86cd799439011")
        assert call_args["actor_name"] == "Test User"
        assert call_args["customer_phone"] == "+1234567890"
        assert call_args["conversation_id"] == ObjectId("507f1f77bcf86cd799439012")
        assert call_args["department_id"] == ObjectId("507f1f77bcf86cd799439013")
        assert call_args["payload"] == {"test": "data"}
        assert call_args["metadata"]["correlation_id"] == "test-correlation-id"
        assert call_args["metadata"]["context"] == "test"
        assert isinstance(call_args["created_at"], datetime)

        # Verify write concern
        call_kwargs = mock_database.db.audit_logs.insert_one.call_args[1]
        assert call_kwargs["write_concern"] == {"w": 1, "j": True}

        # Verify logging
        mock_logger.info.assert_called_once()

    @pytest.mark.asyncio
    async def test_log_event_with_none_values(self, mock_database, mock_logger):
        """Test audit event logging with None values."""
        # Setup
        mock_result = MagicMock()
        mock_result.inserted_id = ObjectId()
        mock_database.db.audit_logs.insert_one.return_value = mock_result

        # Execute
        result = await AuditService.log_event(
            action="test_action",
            actor_id=None,
            actor_name=None,
            customer_phone=None,
            conversation_id=None,
            department_id=None,
            payload=None,
            metadata=None,
            correlation_id=None,
        )

        # Verify
        assert result == str(mock_result.inserted_id)

        # Verify the inserted document handles None values
        call_args = mock_database.db.audit_logs.insert_one.call_args[0][0]
        assert call_args["actor_id"] is None
        assert call_args["actor_name"] is None
        assert call_args["customer_phone"] is None
        assert call_args["conversation_id"] is None
        assert call_args["department_id"] is None
        assert call_args["payload"] == {}
        assert call_args["metadata"] == {}

    @pytest.mark.asyncio
    async def test_log_event_failure(self, mock_database, mock_logger):
        """Test audit event logging failure handling."""
        # Setup
        mock_database.db.audit_logs.insert_one.side_effect = Exception("Database error")

        # Execute
        result = await AuditService.log_event(
            action="test_action", actor_id="507f1f77bcf86cd799439011", actor_name="Test User"
        )

        # Verify
        assert result is None
        mock_logger.error.assert_called_once()
        error_call = mock_logger.error.call_args
        assert "Failed to log audit event" in error_call[0][0]
        assert error_call[1]["exc_info"] is True

    @pytest.mark.asyncio
    async def test_log_message_sent(self, mock_database, mock_logger):
        """Test message sent audit logging."""
        # Setup
        mock_result = MagicMock()
        mock_result.inserted_id = ObjectId()
        mock_database.db.audit_logs.insert_one.return_value = mock_result

        # Execute
        result = await AuditService.log_message_sent(
            actor_id="507f1f77bcf86cd799439011",
            actor_name="Test Agent",
            conversation_id="507f1f77bcf86cd799439012",
            customer_phone="+1234567890",
            department_id="507f1f77bcf86cd799439013",
            message_type="text",
            message_id="507f1f77bcf86cd799439014",
            correlation_id="test-correlation-id",
        )

        # Verify
        assert result == str(mock_result.inserted_id)

        # Verify the audit log content
        call_args = mock_database.db.audit_logs.insert_one.call_args[0][0]
        assert call_args["action"] == "message_sent"
        assert call_args["payload"]["message_type"] == "text"
        assert call_args["payload"]["message_id"] == "507f1f77bcf86cd799439014"

    @pytest.mark.asyncio
    async def test_log_agent_transfer(self, mock_database, mock_logger):
        """Test agent transfer audit logging."""
        # Setup
        mock_result = MagicMock()
        mock_result.inserted_id = ObjectId()
        mock_database.db.audit_logs.insert_one.return_value = mock_result

        # Execute
        result = await AuditService.log_agent_transfer(
            actor_id="507f1f77bcf86cd799439011",
            actor_name="Test Manager",
            conversation_id="507f1f77bcf86cd799439012",
            customer_phone="+1234567890",
            from_department_id="507f1f77bcf86cd799439013",
            to_department_id="507f1f77bcf86cd799439014",
            from_agent_id="507f1f77bcf86cd799439015",
            to_agent_id="507f1f77bcf86cd799439016",
            reason="Customer escalation",
            correlation_id="test-correlation-id",
        )

        # Verify
        assert result == str(mock_result.inserted_id)

        # Verify the audit log content
        call_args = mock_database.db.audit_logs.insert_one.call_args[0][0]
        assert call_args["action"] == "agent_transfer"
        assert call_args["department_id"] == ObjectId(
            "507f1f77bcf86cd799439014"
        )  # to_department_id
        assert call_args["payload"]["from_department_id"] == "507f1f77bcf86cd799439013"
        assert call_args["payload"]["to_department_id"] == "507f1f77bcf86cd799439014"
        assert call_args["payload"]["from_agent_id"] == "507f1f77bcf86cd799439015"
        assert call_args["payload"]["to_agent_id"] == "507f1f77bcf86cd799439016"
        assert call_args["payload"]["reason"] == "Customer escalation"

    @pytest.mark.asyncio
    async def test_log_conversation_closed(self, mock_database, mock_logger):
        """Test conversation closed audit logging."""
        # Setup
        mock_result = MagicMock()
        mock_result.inserted_id = ObjectId()
        mock_database.db.audit_logs.insert_one.return_value = mock_result

        # Execute
        result = await AuditService.log_conversation_closed(
            actor_id="507f1f77bcf86cd799439011",
            actor_name="Test Agent",
            conversation_id="507f1f77bcf86cd799439012",
            customer_phone="+1234567890",
            department_id="507f1f77bcf86cd799439013",
            reason="Issue resolved",
            resolution="Customer satisfied",
            correlation_id="test-correlation-id",
        )

        # Verify
        assert result == str(mock_result.inserted_id)

        # Verify the audit log content
        call_args = mock_database.db.audit_logs.insert_one.call_args[0][0]
        assert call_args["action"] == "conversation_closed"
        assert call_args["payload"]["reason"] == "Issue resolved"
        assert call_args["payload"]["resolution"] == "Customer satisfied"

    @pytest.mark.asyncio
    async def test_log_tag_added(self, mock_database, mock_logger):
        """Test tag added audit logging."""
        # Setup
        mock_result = MagicMock()
        mock_result.inserted_id = ObjectId()
        mock_database.db.audit_logs.insert_one.return_value = mock_result

        # Execute
        result = await AuditService.log_tag_added(
            actor_id="507f1f77bcf86cd799439011",
            actor_name="Test Agent",
            conversation_id="507f1f77bcf86cd799439012",
            customer_phone="+1234567890",
            department_id="507f1f77bcf86cd799439013",
            tag_name="urgent",
            tag_id="507f1f77bcf86cd799439014",
            correlation_id="test-correlation-id",
        )

        # Verify
        assert result == str(mock_result.inserted_id)

        # Verify the audit log content
        call_args = mock_database.db.audit_logs.insert_one.call_args[0][0]
        assert call_args["action"] == "tag_added"
        assert call_args["payload"]["tag_name"] == "urgent"
        assert call_args["payload"]["tag_id"] == "507f1f77bcf86cd799439014"

    @pytest.mark.asyncio
    async def test_log_note_added(self, mock_database, mock_logger):
        """Test note added audit logging."""
        # Setup
        mock_result = MagicMock()
        mock_result.inserted_id = ObjectId()
        mock_database.db.audit_logs.insert_one.return_value = mock_result

        # Execute
        result = await AuditService.log_note_added(
            actor_id="507f1f77bcf86cd799439011",
            actor_name="Test Agent",
            conversation_id="507f1f77bcf86cd799439012",
            customer_phone="+1234567890",
            department_id="507f1f77bcf86cd799439013",
            note_id="507f1f77bcf86cd799439014",
            note_type="internal",
            correlation_id="test-correlation-id",
        )

        # Verify
        assert result == str(mock_result.inserted_id)

        # Verify the audit log content
        call_args = mock_database.db.audit_logs.insert_one.call_args[0][0]
        assert call_args["action"] == "note_added"
        assert call_args["payload"]["note_id"] == "507f1f77bcf86cd799439014"
        assert call_args["payload"]["note_type"] == "internal"

    @pytest.mark.asyncio
    async def test_log_status_changed(self, mock_database, mock_logger):
        """Test status changed audit logging."""
        # Setup
        mock_result = MagicMock()
        mock_result.inserted_id = ObjectId()
        mock_database.db.audit_logs.insert_one.return_value = mock_result

        # Execute
        result = await AuditService.log_status_changed(
            actor_id="507f1f77bcf86cd799439011",
            actor_name="Test Agent",
            conversation_id="507f1f77bcf86cd799439012",
            customer_phone="+1234567890",
            department_id="507f1f77bcf86cd799439013",
            from_status="pending",
            to_status="active",
            correlation_id="test-correlation-id",
        )

        # Verify
        assert result == str(mock_result.inserted_id)

        # Verify the audit log content
        call_args = mock_database.db.audit_logs.insert_one.call_args[0][0]
        assert call_args["action"] == "status_changed"
        assert call_args["payload"]["from_status"] == "pending"
        assert call_args["payload"]["to_status"] == "active"

    @pytest.mark.asyncio
    async def test_log_priority_changed(self, mock_database, mock_logger):
        """Test priority changed audit logging."""
        # Setup
        mock_result = MagicMock()
        mock_result.inserted_id = ObjectId()
        mock_database.db.audit_logs.insert_one.return_value = mock_result

        # Execute
        result = await AuditService.log_priority_changed(
            actor_id="507f1f77bcf86cd799439011",
            actor_name="Test Agent",
            conversation_id="507f1f77bcf86cd799439012",
            customer_phone="+1234567890",
            department_id="507f1f77bcf86cd799439013",
            from_priority="normal",
            to_priority="high",
            correlation_id="test-correlation-id",
        )

        # Verify
        assert result == str(mock_result.inserted_id)

        # Verify the audit log content
        call_args = mock_database.db.audit_logs.insert_one.call_args[0][0]
        assert call_args["action"] == "priority_changed"
        assert call_args["payload"]["from_priority"] == "normal"
        assert call_args["payload"]["to_priority"] == "high"
