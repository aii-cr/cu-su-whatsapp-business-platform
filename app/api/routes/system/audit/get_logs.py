"""
Audit logs retrieval endpoint for WhatsApp Business Platform.
Provides filtered and paginated access to domain-specific audit logs.
"""

from datetime import datetime
from typing import Any, Dict, Optional

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.config.error_codes import ErrorCode
from app.core.logger import logger
from app.core.security import require_permissions
from app.db.models.auth.user import User
from app.schemas.system.audit_log import (
    WhatsAppAuditLogListResponse,
    WhatsAppAuditLogResponse,
)
from app.services import system_audit_service
from app.core.error_handling import handle_database_error

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
        # Convert string IDs to ObjectId
        actor_obj_id = ObjectId(actor_id) if actor_id else None
        conversation_obj_id = ObjectId(conversation_id) if conversation_id else None
        department_obj_id = ObjectId(department_id) if department_id else None
        
        # Get audit logs using service
        result = await system_audit_service.get_audit_logs(
            page=page,
            per_page=per_page,
            action=action,
            actor_id=actor_obj_id,
            actor_name=actor_name,
            customer_phone=customer_phone,
            conversation_id=conversation_obj_id,
            department_id=department_obj_id,
            from_date=from_date,
            to_date=to_date,
            correlation_id=correlation_id,
            sort_by=sort_by,
            sort_order=sort_order
        )
        
        # Convert to response format
        audit_logs = [WhatsAppAuditLogResponse(**log) for log in result["logs"]]
        
        # Log the request
        logger.info(
            f"Retrieved {len(audit_logs)} audit logs",
            extra={
                "user_id": str(current_user.id),
                "page": result["page"],
                "per_page": result["per_page"],
                "total_count": result["total"],
                "filters": result["filters"],
            },
        )
        
        return WhatsAppAuditLogListResponse(
            logs=audit_logs,
            total=result["total"],
            page=result["page"],
            per_page=result["per_page"],
            pages=result["pages"],
        )
        
    except ValueError as e:
        logger.warning(f"Invalid query parameters: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail=f"Invalid query parameters: {str(e)}"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Failed to retrieve audit logs: {str(e)}",
            extra={"user_id": str(current_user.id)},
            exc_info=True,
        )
        raise handle_database_error(e, "get_audit_logs", "audit_logs")
