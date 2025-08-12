"""Get tag endpoint."""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse

from app.config.error_codes import ErrorCode, get_error_response
from app.core.logger import logger
from app.services.auth import require_permissions
from app.db.models.auth import User
from app.schemas.whatsapp.chat.tag import TagResponse
from app.services import tag_service
from app.core.error_handling import handle_database_error
from app.core.middleware import get_correlation_id
from bson import ObjectId

router = APIRouter()

@router.get("/{tag_id}", response_model=TagResponse)
async def get_tag(
    tag_id: str,
    current_user: User = Depends(require_permissions(["tags:read"]))
):
    """
    Get a specific tag by ID.
    
    Args:
        tag_id: ID of the tag to retrieve
        current_user: Current authenticated user
        
    Returns:
        Tag details
    """
    correlation_id = get_correlation_id()
    
    try:
        # Validate tag_id
        try:
            tag_object_id = ObjectId(tag_id)
        except Exception:
            return get_error_response(ErrorCode.INVALID_ID, "Invalid tag ID format")
        
        logger.info(
            f"🔍 [GET_TAG] Getting tag: {tag_id}",
            extra={
                "user_id": str(current_user.id),
                "tag_id": tag_id,
                "correlation_id": correlation_id
            }
        )
        
        # Get tag using service
        tag = await tag_service.get_tag(tag_object_id)
        
        if not tag:
            return get_error_response(ErrorCode.TAG_NOT_FOUND, "Tag not found")
        
        # Convert to response format
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
        
        logger.info(
            f"✅ [GET_TAG] Found tag: {tag['name']} (ID: {tag_id})",
            extra={
                "user_id": str(current_user.id),
                "tag_id": tag_id,
                "tag_name": tag["name"],
                "correlation_id": correlation_id
            }
        )
        
        return tag_response
        
    except HTTPException:
        raise
        
    except Exception as e:
        logger.error(
            f"❌ [GET_TAG] Unexpected error: {str(e)}",
            extra={
                "user_id": str(current_user.id),
                "tag_id": tag_id,
                "error": str(e),
                "correlation_id": correlation_id
            }
        )
        raise handle_database_error(e, "get_tag", "tag")



