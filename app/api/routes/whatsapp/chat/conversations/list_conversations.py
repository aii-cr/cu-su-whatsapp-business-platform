"""List conversations endpoint."""

from fastapi import APIRouter, Depends, HTTPException, status

from app.schemas.whatsapp.chat import ConversationListResponse, ConversationQueryParams, ConversationResponse
from app.services.auth import require_permissions
from app.db.models.auth import User
from app.db.client import database
from app.config.error_codes import ErrorCode
from app.core.logger import logger

router = APIRouter()

@router.get("/", response_model=ConversationListResponse)
async def list_conversations(
    params: ConversationQueryParams = Depends(),
    current_user: User = Depends(require_permissions(["conversations:read"]))
):
    """
    List conversations with filtering and pagination.
    Requires 'conversations:read' permission.
    """
    db = database.db
    
    try:
        # Build query
        query = {}
        if params.search:
            query["$or"] = [
                {"customer_name": {"$regex": params.search, "$options": "i"}},
                {"customer_phone": {"$regex": params.search, "$options": "i"}}
            ]
        if params.status:
            query["status"] = params.status
        if params.priority:
            query["priority"] = params.priority
        if params.channel:
            query["channel"] = params.channel
        if params.department_id:
            query["department_id"] = params.department_id
        if params.assigned_agent_id:
            query["assigned_agent_id"] = params.assigned_agent_id
        if params.customer_type:
            query["customer_type"] = params.customer_type
        if params.has_unread:
            query["unread_count"] = {"$gt": 0} if params.has_unread else {"$eq": 0}
        if params.created_from:
            query.setdefault("created_at", {})["$gte"] = params.created_from
        if params.created_to:
            query.setdefault("created_at", {})["$lte"] = params.created_to
        if params.tags:
            query["tags"] = {"$in": params.tags}
        
        # Count total
        total = await db.conversations.count_documents(query)
        
        # Calculate pagination
        skip = (params.page - 1) * params.per_page
        pages = (total + params.per_page - 1) // params.per_page
        
        # Get conversations
        sort_order = 1 if params.sort_order == "asc" else -1
        conversations = await db.conversations.find(query).sort(
            params.sort_by, sort_order
        ).skip(skip).limit(params.per_page).to_list(params.per_page)
        
        return ConversationListResponse(
            conversations=[ConversationResponse(**conv) for conv in conversations],
            total=total,
            page=params.page,
            per_page=params.per_page,
            pages=pages
        )
        
    except Exception as e:
        logger.error(f"Failed to list conversations: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorCode.INTERNAL_SERVER_ERROR
        ) 