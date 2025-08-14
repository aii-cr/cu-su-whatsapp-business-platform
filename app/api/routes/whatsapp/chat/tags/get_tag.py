"""Get tag by ID endpoint following project patterns."""

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, status

from app.config.error_codes import ErrorCode
from app.core.logger import logger
from app.db.models.auth import User
from app.schemas.whatsapp.chat.tag import TagResponse
from app.services.auth import require_permissions
from app.services.whatsapp.tag_service import tag_service
from app.core.error_handling import handle_database_error

router = APIRouter()


@router.get("/{tag_id}", response_model=TagResponse)
async def get_tag(
    tag_id: str,
    current_user: User = Depends(require_permissions(["messages:send"]))
):
    """
    Get a specific tag by ID.
    
    Requires 'messages:send' permission.
    """
    logger.info(f"🏷️ [GET_TAG] Getting tag: {tag_id}")
    logger.info(f"👤 [GET_TAG] User: {current_user.email} (ID: {current_user.id})")
    
    try:
        # Validate ObjectId
        try:
            tag_object_id = ObjectId(tag_id)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid tag ID format"
            )
        
        # Get tag
        tag = await tag_service.get_tag(tag_object_id)
        if not tag:
            logger.error(f"❌ [GET_TAG] Tag not found: {tag_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tag not found"
            )
        
        # Convert to response format
        tag_response = TagResponse(
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
        )
        
        logger.info(f"✅ [GET_TAG] Found tag: {tag['name']}")
        
        return tag_response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ [GET_TAG] Unexpected error: {str(e)}")
        raise handle_database_error(e, "get_tag", "tag")

