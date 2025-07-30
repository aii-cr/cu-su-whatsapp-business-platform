"""List conversations endpoint."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import Optional

from app.config.error_codes import ErrorCode
from app.core.logger import logger
from app.services.auth import require_permissions
from app.db.models.auth import User
from app.schemas.whatsapp.chat.conversation import ConversationListResponse
from app.services import conversation_service
from app.core.error_handling import handle_database_error

router = APIRouter()

@router.get("/", response_model=ConversationListResponse)
async def list_conversations(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search by customer phone or name"),
    status: Optional[str] = Query(None, description="Filter by conversation status"),
    priority: Optional[str] = Query(None, description="Filter by priority"),
    channel: Optional[str] = Query(None, description="Filter by channel"),
    department_id: Optional[str] = Query(None, description="Filter by department ID"),
    assigned_agent_id: Optional[str] = Query(None, description="Filter by assigned agent ID"),
    customer_type: Optional[str] = Query(None, description="Filter by customer type"),
    has_unread: Optional[bool] = Query(None, description="Filter by unread status"),
    sort_by: str = Query("updated_at", description="Sort field"),
    sort_order: str = Query("desc", regex="^(asc|desc)$", description="Sort order"),
    current_user: User = Depends(require_permissions(["conversations:read"])),
):
    """
    List conversations with filtering and pagination.
    
    Args:
        page: Page number
        per_page: Items per page
        search: Search term for customer phone or name
        status: Filter by conversation status
        priority: Filter by priority
        channel: Filter by channel
        department_id: Filter by department ID
        assigned_agent_id: Filter by assigned agent ID
        customer_type: Filter by customer type
        has_unread: Filter by unread status
        sort_by: Sort field
        sort_order: Sort order (asc/desc)
        current_user: Current authenticated user
        
    Returns:
        List of conversations with pagination info
    """
    try:
        # Get conversations using service
        result = await conversation_service.list_conversations(
            search=search,
            status=status,
            priority=priority,
            channel=channel,
            department_id=department_id,
            assigned_agent_id=assigned_agent_id,
            customer_type=customer_type,
            has_unread=has_unread,
            sort_by=sort_by,
            sort_order=sort_order,
            page=page,
            per_page=per_page
        )
        
        logger.info(f"Retrieved {len(result['conversations'])} conversations for user {current_user.id}")
        
        return ConversationListResponse(
            conversations=result["conversations"],
            total=result["total"],
            page=result["page"],
            per_page=result["per_page"],
            pages=result["pages"]
        )
        
    except Exception as e:
        logger.error(f"Error retrieving conversations: {str(e)}")
        raise handle_database_error(e, "list_conversations", "conversations") 