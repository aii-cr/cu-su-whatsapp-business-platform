"""List tags endpoint following project patterns."""

from typing import Optional
from fastapi import APIRouter, Depends, Query

from app.core.logger import logger
from app.db.models.auth import User
from app.schemas.whatsapp.chat.tag import TagListResponse, TagResponse, TagStatus
from app.services.auth import require_permissions
from app.services.whatsapp.tag_service import tag_service
from app.core.error_handling import handle_database_error

router = APIRouter()


@router.get("/", response_model=TagListResponse)
async def list_tags(
    limit: int = Query(default=20, ge=1, le=100, description="Number of tags to return"),
    offset: int = Query(default=0, ge=0, description="Number of tags to skip"),
    search: Optional[str] = Query(default=None, description="Search query"),
    category: Optional[str] = Query(default=None, description="Filter by category"),
    status: str = Query(default=TagStatus.ACTIVE, description="Filter by status"),
    sort_by: str = Query(default="usage_count", description="Sort field"),
    sort_order: str = Query(default="desc", description="Sort order (asc/desc)"),
    current_user: User = Depends(require_permissions(["messages:send"]))
):
    """
    List tags with filtering, searching, and pagination.
    
    Requires 'messages:send' permission.
    """
    logger.info(f"🏷️ [LIST_TAGS] Listing tags: limit={limit}, offset={offset}, search='{search}'")
    logger.info(f"👤 [LIST_TAGS] User: {current_user.email} (ID: {current_user.id})")
    
    try:
        # Get tags and total count
        tags, total = await tag_service.list_tags(
            limit=limit,
            offset=offset,
            search=search,
            category=category,
            status=status,
            sort_by=sort_by,
            sort_order=sort_order
        )
        
        # Convert to response format
        tag_responses = []
        for tag in tags:
            tag_responses.append(TagResponse(
                id=str(tag["_id"]),
                name=tag["name"],
                slug=tag["slug"],
                display_name=tag.get("display_name"),
                description=tag.get("description"),
                category=tag["category"],
                color=tag["color"],
                parent_tag_id=str(tag["parent_tag_id"]) if tag.get("parent_tag_id") else None,
                child_tags=[str(child_id) for child_id in tag.get("child_tags", [])],
                status=tag["status"],
                is_system_tag=tag["is_system_tag"],
                is_auto_assignable=tag["is_auto_assignable"],
                usage_count=tag["usage_count"],
                department_ids=[str(dept_id) for dept_id in tag.get("department_ids", [])],
                user_ids=[str(user_id) for user_id in tag.get("user_ids", [])],
                created_at=tag["created_at"].isoformat(),
                updated_at=tag["updated_at"].isoformat(),
                created_by=str(tag["created_by"]) if tag.get("created_by") else None,
                updated_by=str(tag["updated_by"]) if tag.get("updated_by") else None
            ))
        
        logger.info(f"✅ [LIST_TAGS] Found {len(tag_responses)} tags (total: {total})")
        
        return TagListResponse(
            tags=tag_responses,
            total=total,
            limit=limit,
            offset=offset,
            has_more=(offset + limit) < total
        )
        
    except Exception as e:
        logger.error(f"❌ [LIST_TAGS] Unexpected error: {str(e)}")
        raise handle_database_error(e, "list_tags", "tag")

