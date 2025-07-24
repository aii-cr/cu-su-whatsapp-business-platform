"""
Unit tests for the audit logs retrieval endpoint.
Tests API functionality, filtering, pagination, and permissions.
"""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from bson import ObjectId
from fastapi import status
from fastapi.testclient import TestClient

from app.main import app


class TestGetAuditLogs:
    """Test cases for GET /system/audit/logs endpoint."""

    @pytest.fixture
    def client(self):
        """Test client fixture."""
        return TestClient(app)

    @pytest.fixture
    def mock_user(self):
        """Mock authenticated user fixture."""
        mock_user = MagicMock()
        mock_user.id = ObjectId("507f1f77bcf86cd799439011")
        mock_user.email = "test@example.com"
        mock_user.name = "Test User"
        return mock_user

    @pytest.fixture
    def mock_database(self):
        """Mock database fixture."""
        with patch("app.api.routes.system.audit.get_logs.database") as mock_db:
            mock_db.db.audit_logs = AsyncMock()
            yield mock_db

    @pytest.fixture
    def mock_permissions(self):
        """Mock permissions check."""
        with patch("app.api.routes.system.audit.get_logs.require_permissions") as mock_perm:
            yield mock_perm

    @pytest.fixture
    def sample_audit_logs(self):
        """Sample audit log data."""
        return [
            {
                "_id": ObjectId("507f1f77bcf86cd799439011"),
                "conversation_id": ObjectId("507f1f77bcf86cd799439012"),
                "customer_phone": "+1234567890",
                "actor_id": ObjectId("507f1f77bcf86cd799439013"),
                "actor_name": "Test Agent",
                "department_id": ObjectId("507f1f77bcf86cd799439014"),
                "action": "message_sent",
                "payload": {"message_type": "text", "message_id": "507f1f77bcf86cd799439015"},
                "created_at": datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
                "metadata": {"correlation_id": "test-correlation-id"},
            },
            {
                "_id": ObjectId("507f1f77bcf86cd799439016"),
                "conversation_id": ObjectId("507f1f77bcf86cd799439017"),
                "customer_phone": "+1234567891",
                "actor_id": ObjectId("507f1f77bcf86cd799439018"),
                "actor_name": "Test Manager",
                "department_id": ObjectId("507f1f77bcf86cd799439019"),
                "action": "agent_transfer",
                "payload": {
                    "from_agent_id": "507f1f77bcf86cd799439020",
                    "to_agent_id": "507f1f77bcf86cd799439021",
                },
                "created_at": datetime(2024, 1, 1, 13, 0, 0, tzinfo=timezone.utc),
                "metadata": {"correlation_id": "test-correlation-id-2"},
            },
        ]

    @pytest.mark.asyncio
    async def test_get_audit_logs_success(
        self, mock_database, mock_permissions, mock_user, sample_audit_logs
    ):
        """Test successful audit logs retrieval."""
        # Setup
        mock_permissions.return_value = lambda: mock_user

        # Mock database responses
        mock_cursor = AsyncMock()
        mock_cursor.to_list.return_value = sample_audit_logs
        mock_database.db.audit_logs.find.return_value.sort.return_value.skip.return_value.limit.return_value = (
            mock_cursor
        )
        mock_database.db.audit_logs.count_documents.return_value = 2

        # Mock get_correlation_id
        with patch("app.api.routes.system.audit.get_logs.get_correlation_id") as mock_correlation:
            mock_correlation.return_value = "test-correlation-id"

            # Import the function directly for testing
            from app.api.routes.system.audit.get_logs import get_audit_logs

            # Execute
            result = await get_audit_logs(page=1, per_page=50, current_user=mock_user)

        # Verify
        assert result.total == 2
        assert result.page == 1
        assert result.per_page == 50
        assert result.pages == 1
        assert len(result.logs) == 2

        # Verify database calls
        mock_database.db.audit_logs.find.assert_called_once()
        mock_database.db.audit_logs.count_documents.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_audit_logs_with_filters(
        self, mock_database, mock_permissions, mock_user, sample_audit_logs
    ):
        """Test audit logs retrieval with filters."""
        # Setup
        mock_permissions.return_value = lambda: mock_user

        # Mock database responses
        mock_cursor = AsyncMock()
        mock_cursor.to_list.return_value = [sample_audit_logs[0]]  # Only first log matches filter
        mock_database.db.audit_logs.find.return_value.sort.return_value.skip.return_value.limit.return_value = (
            mock_cursor
        )
        mock_database.db.audit_logs.count_documents.return_value = 1

        # Mock get_correlation_id
        with patch("app.api.routes.system.audit.get_logs.get_correlation_id") as mock_correlation:
            mock_correlation.return_value = "test-correlation-id"

            # Import the function directly for testing
            from app.api.routes.system.audit.get_logs import get_audit_logs

            # Execute with filters
            result = await get_audit_logs(
                page=1,
                per_page=50,
                action="message_sent",
                actor_name="Test Agent",
                customer_phone="+1234567890",
                current_user=mock_user,
            )

        # Verify
        assert result.total == 1
        assert len(result.logs) == 1
        assert result.logs[0].action == "message_sent"

        # Verify the query was built with filters
        call_args = mock_database.db.audit_logs.find.call_args[0][0]
        assert call_args["action"] == "message_sent"
        assert call_args["actor_name"]["$regex"] == "Test Agent"
        assert call_args["customer_phone"] == "+1234567890"

    @pytest.mark.asyncio
    async def test_get_audit_logs_with_date_range(
        self, mock_database, mock_permissions, mock_user, sample_audit_logs
    ):
        """Test audit logs retrieval with date range filter."""
        # Setup
        mock_permissions.return_value = lambda: mock_user

        # Mock database responses
        mock_cursor = AsyncMock()
        mock_cursor.to_list.return_value = sample_audit_logs
        mock_database.db.audit_logs.find.return_value.sort.return_value.skip.return_value.limit.return_value = (
            mock_cursor
        )
        mock_database.db.audit_logs.count_documents.return_value = 2

        # Date range
        from_date = datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
        to_date = datetime(2024, 1, 1, 23, 59, 59, tzinfo=timezone.utc)

        # Mock get_correlation_id
        with patch("app.api.routes.system.audit.get_logs.get_correlation_id") as mock_correlation:
            mock_correlation.return_value = "test-correlation-id"

            # Import the function directly for testing
            from app.api.routes.system.audit.get_logs import get_audit_logs

            # Execute with date range
            result = await get_audit_logs(
                page=1, per_page=50, from_date=from_date, to_date=to_date, current_user=mock_user
            )

        # Verify
        assert result.total == 2

        # Verify the query was built with date range
        call_args = mock_database.db.audit_logs.find.call_args[0][0]
        assert "created_at" in call_args
        assert call_args["created_at"]["$gte"] == from_date
        assert call_args["created_at"]["$lte"] == to_date

    @pytest.mark.asyncio
    async def test_get_audit_logs_pagination(
        self, mock_database, mock_permissions, mock_user, sample_audit_logs
    ):
        """Test audit logs pagination."""
        # Setup
        mock_permissions.return_value = lambda: mock_user

        # Mock database responses
        mock_cursor = AsyncMock()
        mock_cursor.to_list.return_value = [sample_audit_logs[1]]  # Second page, one item
        mock_database.db.audit_logs.find.return_value.sort.return_value.skip.return_value.limit.return_value = (
            mock_cursor
        )
        mock_database.db.audit_logs.count_documents.return_value = 51  # Total more than one page

        # Mock get_correlation_id
        with patch("app.api.routes.system.audit.get_logs.get_correlation_id") as mock_correlation:
            mock_correlation.return_value = "test-correlation-id"

            # Import the function directly for testing
            from app.api.routes.system.audit.get_logs import get_audit_logs

            # Execute with pagination
            result = await get_audit_logs(page=2, per_page=50, current_user=mock_user)

        # Verify
        assert result.total == 51
        assert result.page == 2
        assert result.per_page == 50
        assert result.pages == 2  # ceil(51/50) = 2

        # Verify pagination was applied in database query
        mock_database.db.audit_logs.find.return_value.sort.return_value.skip.assert_called_with(
            50
        )  # Skip first 50 for page 2
        mock_database.db.audit_logs.find.return_value.sort.return_value.skip.return_value.limit.assert_called_with(
            50
        )

    @pytest.mark.asyncio
    async def test_get_audit_logs_sorting(
        self, mock_database, mock_permissions, mock_user, sample_audit_logs
    ):
        """Test audit logs sorting."""
        # Setup
        mock_permissions.return_value = lambda: mock_user

        # Mock database responses
        mock_cursor = AsyncMock()
        mock_cursor.to_list.return_value = sample_audit_logs
        mock_database.db.audit_logs.find.return_value.sort.return_value.skip.return_value.limit.return_value = (
            mock_cursor
        )
        mock_database.db.audit_logs.count_documents.return_value = 2

        # Mock get_correlation_id
        with patch("app.api.routes.system.audit.get_logs.get_correlation_id") as mock_correlation:
            mock_correlation.return_value = "test-correlation-id"

            # Import the function directly for testing
            from app.api.routes.system.audit.get_logs import get_audit_logs

            # Execute with custom sorting
            result = await get_audit_logs(
                page=1, per_page=50, sort_by="action", sort_order="asc", current_user=mock_user
            )

        # Verify
        assert result.total == 2

        # Verify sorting was applied
        mock_database.db.audit_logs.find.return_value.sort.assert_called_with(
            [("action", 1)]
        )  # 1 for ascending

    @pytest.mark.asyncio
    async def test_get_audit_logs_invalid_object_id(
        self, mock_database, mock_permissions, mock_user
    ):
        """Test audit logs with invalid ObjectId."""
        # Setup
        mock_permissions.return_value = lambda: mock_user

        # Mock get_correlation_id
        with patch("app.api.routes.system.audit.get_logs.get_correlation_id") as mock_correlation:
            mock_correlation.return_value = "test-correlation-id"

            # Import the function directly for testing
            from app.api.routes.system.audit.get_logs import get_audit_logs

            # Execute with invalid ObjectId - should raise HTTPException
            with pytest.raises(
                Exception
            ):  # ValueError will be caught and converted to HTTPException
                await get_audit_logs(
                    page=1, per_page=50, actor_id="invalid-object-id", current_user=mock_user
                )

    @pytest.mark.asyncio
    async def test_get_audit_logs_database_error(self, mock_database, mock_permissions, mock_user):
        """Test audit logs with database error."""
        # Setup
        mock_permissions.return_value = lambda: mock_user
        mock_database.db.audit_logs.find.side_effect = Exception("Database connection error")

        # Mock get_correlation_id
        with patch("app.api.routes.system.audit.get_logs.get_correlation_id") as mock_correlation:
            mock_correlation.return_value = "test-correlation-id"

            # Import the function directly for testing
            from app.api.routes.system.audit.get_logs import get_audit_logs

            # Execute - should raise HTTPException
            with pytest.raises(
                Exception
            ):  # Database error will be caught and converted to HTTPException
                await get_audit_logs(page=1, per_page=50, current_user=mock_user)

    def test_build_mongo_query_basic(self):
        """Test building basic MongoDB query."""
        from app.api.routes.system.audit.get_logs import _build_mongo_query
        from app.schemas.system.audit_log import WhatsAppAuditQueryParams

        # Execute
        params = WhatsAppAuditQueryParams(
            page=1, per_page=50, action="message_sent", customer_phone="+1234567890"
        )

        import asyncio

        query = asyncio.run(_build_mongo_query(params))

        # Verify
        assert query["action"] == "message_sent"
        assert query["customer_phone"] == "+1234567890"

    def test_build_mongo_query_with_object_ids(self):
        """Test building MongoDB query with ObjectIds."""
        from app.api.routes.system.audit.get_logs import _build_mongo_query
        from app.schemas.system.audit_log import WhatsAppAuditQueryParams

        # Execute
        params = WhatsAppAuditQueryParams(
            page=1,
            per_page=50,
            actor_id=ObjectId("507f1f77bcf86cd799439011"),
            conversation_id=ObjectId("507f1f77bcf86cd799439012"),
            department_id=ObjectId("507f1f77bcf86cd799439013"),
        )

        import asyncio

        query = asyncio.run(_build_mongo_query(params))

        # Verify
        assert query["actor_id"] == ObjectId("507f1f77bcf86cd799439011")
        assert query["conversation_id"] == ObjectId("507f1f77bcf86cd799439012")
        assert query["department_id"] == ObjectId("507f1f77bcf86cd799439013")

    def test_build_mongo_query_with_date_range(self):
        """Test building MongoDB query with date range."""
        from app.api.routes.system.audit.get_logs import _build_mongo_query
        from app.schemas.system.audit_log import WhatsAppAuditQueryParams

        # Execute
        from_date = datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
        to_date = datetime(2024, 1, 31, 23, 59, 59, tzinfo=timezone.utc)

        params = WhatsAppAuditQueryParams(page=1, per_page=50, from_date=from_date, to_date=to_date)

        import asyncio

        query = asyncio.run(_build_mongo_query(params))

        # Verify
        assert "created_at" in query
        assert query["created_at"]["$gte"] == from_date
        assert query["created_at"]["$lte"] == to_date

    def test_build_sort_criteria(self):
        """Test building sort criteria."""
        from app.api.routes.system.audit.get_logs import _build_sort_criteria
        from app.schemas.system.audit_log import WhatsAppAuditQueryParams

        # Test descending sort
        params = WhatsAppAuditQueryParams(
            page=1, per_page=50, sort_by="created_at", sort_order="desc"
        )

        import asyncio

        sort_criteria = asyncio.run(_build_sort_criteria(params))

        assert sort_criteria == [("created_at", -1)]

        # Test ascending sort
        params.sort_order = "asc"
        sort_criteria = asyncio.run(_build_sort_criteria(params))

        assert sort_criteria == [("created_at", 1)]

        # Test invalid sort field defaults to created_at
        params.sort_by = "invalid_field"
        sort_criteria = asyncio.run(_build_sort_criteria(params))

        assert sort_criteria == [("created_at", 1)]
