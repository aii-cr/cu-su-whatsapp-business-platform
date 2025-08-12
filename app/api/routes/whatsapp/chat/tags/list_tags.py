"""List tags endpoint with filtering and search."""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse

from app.config.error_codes import ErrorCode, get_error_response
from app.core.logger import logger
from app.services.auth import require_permissions
from app.db.models.auth import User
from app.schemas.whatsapp.chat.tag import TagListRequest, TagListResponse, TagResponse
from app.services import tag_service
from app.core.error_handling import handle_database_error
from app.core.middleware import get_correlation_id

router = APIRouter()

@router.get("/", response_model=TagListResponse)
async def list_tags(
    category: str = None,
    status: str = None,
    department_id: str = None,
    search: str = None,
    parent_tag_id: str = None,
    limit: int = 50,
    offset: int = 0,
    sort_by: str = "name",
    sort_order: str = "asc",
    current_user: User = Depends(require_permissions(["tags:read"]))
):
    """
    List tags with filtering, searching, and pagination.
    
    Args:
        category: Filter by tag category
        status: Filter by tag status (active/inactive)
        department_id: Filter by department access
        search: Search query for tag names
        parent_tag_id: Filter by parent tag
        limit: Maximum results (1-200)
        offset: Results offset
        sort_by: Sort field (name, category, usage_count, created_at, updated_at)
        sort_order: Sort order (asc/desc)
        current_user: Current authenticated user
        
    Returns:
        Paginated list of tags
    """
    correlation_id = get_correlation_id()
    
    try:
        logger.info(
            f"📋 [LIST_TAGS] Listing tags",
            extra={
                "user_id": str(current_user.id),
                "category": category,
                "search": search,
                "limit": limit,
                "offset": offset,
                "correlation_id": correlation_id
            }
        )
        
        # Build list request
        list_request = TagListRequest(
            category=category,
            status=status,
            department_id=department_id,
            search=search,
            parent_tag_id=parent_tag_id,
            limit=limit,
            offset=offset,
            sort_by=sort_by,
            sort_order=sort_order
        )
        
        # Get tags from service
        tags, total = await tag_service.list_tags(list_request)
        
        # Convert to response format
        tag_responses = []
        for tag in tags:
            tag_response = TagResponse(
                _id=str(tag["_id"]),
                name=tag["name"],
                slug=tag["slug"],
                display_name=tag.get("display_name"),
                description=tag.get("description"),
                category=tag["category"],
                color=tag["color"],
                parent_tag_id=str(tag["parent_tag_id"]) if tag.get("parent_tag_id") else None,
                child_tags=[str(cid) for cid in tag.get("child_tags", [])],
                status=tag["status"],
                is_system_tag=tag.get("is_system_tag", False),
                is_auto_assignable=tag.get("is_auto_assignable", True),
                usage_count=tag.get("usage_count", 0),
                department_ids=[str(did) for did in tag.get("department_ids", [])],
                user_ids=[str(uid) for uid in tag.get("user_ids", [])],
                created_at=tag["created_at"],
                updated_at=tag["updated_at"],
                created_by=str(tag["created_by"]) if tag.get("created_by") else None,
                updated_by=str(tag["updated_by"]) if tag.get("updated_by") else None
            )
            tag_responses.append(tag_response)
        
        # Build response
        response = TagListResponse(
            tags=tag_responses,
            total=total,
            limit=limit,
            offset=offset,
            has_more=(offset + limit) < total
        )
        
        logger.info(
            f"✅ [LIST_TAGS] Found {len(tag_responses)} tags (total: {total})",
            extra={
                "user_id": str(current_user.id),
                "tags_count": len(tag_responses),
                "total": total,
                "correlation_id": correlation_id
            }
        )
        
        return response
        
    except ValueError as e:
        logger.warning(
            f"⚠️ [LIST_TAGS] Validation error: {str(e)}",
            extra={
                "user_id": str(current_user.id),
                "error": str(e),
                "correlation_id": correlation_id
            }
        )
        return get_error_response(ErrorCode.VALIDATION_ERROR, str(e))
        
    except HTTPException:
        raise
        
    except Exception as e:
        logger.error(
            f"❌ [LIST_TAGS] Unexpected error: {str(e)}",
            extra={
                "user_id": str(current_user.id),
                "error": str(e),
                "correlation_id": correlation_id
            }
        )
        raise handle_database_error(e, "list_tags", "tags")



