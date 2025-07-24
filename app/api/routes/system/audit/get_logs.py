"""
Audit logs retrieval endpoint for WhatsApp Business Platform.
Provides filtered and paginated access to domain-specific audit logs.
"""

import math
from datetime import datetime
from typing import Any, Dict, Optional

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Query, status
from motor.motor_asyncio import AsyncIOMotorCollection

from app.config.error_codes import ErrorCode
from app.core.logger import logger
from app.core.security import require_permissions
from app.db.client import database
from app.db.models.auth.user import User
from app.schemas.system.audit_log import (
    WhatsAppAuditLogListResponse,
    WhatsAppAuditLogResponse,
    WhatsAppAuditQueryParams,
)

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("/logs", response_model=WhatsAppAuditLogListResponse)
async def get_audit_logs(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(50, ge=1, le=200, description="Items per page"),
    action: Optional[str] = Query(None, description="Filter by action type"),
    actor_id: Optional[str] = Query(None, description="Filter by actor ID"),
    actor_name: Optional[str] = Query(None, description="Filter by actor name"),
    customer_phone: Optional[str] = Query(None, description="Filter by customer phone"),
    conversation_id: Optional[str] = Query(None, description="Filter by conversation ID"),
    department_id: Optional[str] = Query(None, description="Filter by department ID"),
    from_date: Optional[datetime] = Query(None, description="Filter logs from this date"),
    to_date: Optional[datetime] = Query(None, description="Filter logs to this date"),
    correlation_id: Optional[str] = Query(None, description="Filter by correlation ID"),
    sort_by: str = Query("created_at", description="Sort field"),
    sort_order: str = Query("desc", regex="^(asc|desc)$", description="Sort order"),
    current_user: User = Depends(require_permissions(["audit:read"])),
):
    """
    Retrieve audit logs with filtering and pagination.

    This endpoint provides access to domain-specific WhatsApp Business audit logs
    with comprehensive filtering options and pagination support.

    Required permissions: audit:read
    """
    try:
        # Validate and build query parameters
        query_params = WhatsAppAuditQueryParams(
            page=page,
            per_page=per_page,
            action=action,
            actor_id=ObjectId(actor_id) if actor_id else None,
            actor_name=actor_name,
            customer_phone=customer_phone,
            conversation_id=ObjectId(conversation_id) if conversation_id else None,
            department_id=ObjectId(department_id) if department_id else None,
            from_date=from_date,
            to_date=to_date,
            correlation_id=correlation_id,
            sort_by=sort_by,
            sort_order=sort_order,
        )

        # Build MongoDB query
        mongo_query = await _build_mongo_query(query_params)

        # Build sort criteria
        sort_criteria = await _build_sort_criteria(query_params)

        # Get collection
        collection: AsyncIOMotorCollection = database.db.audit_logs

        # Calculate pagination
        skip = (query_params.page - 1) * query_params.per_page
        limit = query_params.per_page

        # Execute queries in parallel
        logs_cursor = collection.find(mongo_query).sort(sort_criteria).skip(skip).limit(limit)
        logs = await logs_cursor.to_list(length=limit)
        total_count = await collection.count_documents(mongo_query)

        # Convert to response format
        audit_logs = [WhatsAppAuditLogResponse(**log) for log in logs]

        # Calculate total pages
        total_pages = math.ceil(total_count / query_params.per_page)

        # Log the request
        logger.info(
            f"Retrieved {len(audit_logs)} audit logs",
            extra={
                "user_id": str(current_user.id),
                "page": query_params.page,
                "per_page": query_params.per_page,
                "total_count": total_count,
                "filters": {
                    "action": query_params.action,
                    "actor_id": query_params.actor_id,
                    "conversation_id": query_params.conversation_id,
                    "from_date": query_params.from_date,
                    "to_date": query_params.to_date,
                },
            },
        )

        return WhatsAppAuditLogListResponse(
            logs=audit_logs,
            total=total_count,
            page=query_params.page,
            per_page=query_params.per_page,
            pages=total_pages,
        )

    except ValueError as e:
        logger.warning(f"Invalid query parameters: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid query parameters: {str(e)}"
        )
    except Exception as e:
        logger.error(
            f"Failed to retrieve audit logs: {str(e)}",
            extra={"user_id": str(current_user.id)},
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorCode.INTERNAL_SERVER_ERROR,
        )


async def _build_mongo_query(params: WhatsAppAuditQueryParams) -> Dict[str, Any]:
    """
    Build MongoDB query from query parameters.

    Args:
        params: Validated query parameters

    Returns:
        MongoDB query dictionary
    """
    query = {}

    # Filter by action
    if params.action:
        query["action"] = params.action

    # Filter by actor
    if params.actor_id:
        query["actor_id"] = params.actor_id

    if params.actor_name:
        query["actor_name"] = {"$regex": params.actor_name, "$options": "i"}

    # Filter by customer phone
    if params.customer_phone:
        query["customer_phone"] = params.customer_phone

    # Filter by conversation
    if params.conversation_id:
        query["conversation_id"] = params.conversation_id

    # Filter by department
    if params.department_id:
        query["department_id"] = params.department_id

    # Filter by date range
    date_filter = {}
    if params.from_date:
        date_filter["$gte"] = params.from_date
    if params.to_date:
        date_filter["$lte"] = params.to_date

    if date_filter:
        query["created_at"] = date_filter

    # Filter by correlation ID in metadata
    if params.correlation_id:
        query["metadata.correlation_id"] = params.correlation_id

    return query


async def _build_sort_criteria(params: WhatsAppAuditQueryParams) -> list:
    """
    Build MongoDB sort criteria from query parameters.

    Args:
        params: Validated query parameters

    Returns:
        MongoDB sort criteria list
    """
    # Validate sort field
    valid_sort_fields = ["created_at", "action", "actor_name", "customer_phone"]

    sort_field = params.sort_by if params.sort_by in valid_sort_fields else "created_at"
    sort_direction = -1 if params.sort_order == "desc" else 1

    return [(sort_field, sort_direction)]
