"""Create tag endpoint."""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse

from app.config.error_codes import ErrorCode, get_error_response
from app.core.logger import logger
from app.services.auth import require_permissions
from app.db.models.auth import User
from app.schemas.whatsapp.chat.tag import TagCreate, TagResponse
from app.services import tag_service, audit_service
from app.core.error_handling import handle_database_error
from app.core.middleware import get_correlation_id
from bson import ObjectId

router = APIRouter()

@router.post("/", response_model=TagResponse, status_code=status.HTTP_201_CREATED)
async def create_tag(
    tag_data: TagCreate,
    current_user: User = Depends(require_permissions(["tags:write"]))
):
    """
    Create a new tag.
    
    Args:
        tag_data: Tag creation data
        current_user: Current authenticated user
        
    Returns:
        Created tag details
    """
    correlation_id = get_correlation_id()
    
    try:
        logger.info(
            f"➕ [CREATE_TAG] Creating tag: {tag_data.name}",
            extra={
                "user_id": str(current_user.id),
                "tag_name": tag_data.name,
                "category": tag_data.category,
                "correlation_id": correlation_id
            }
        )
        
        # Create tag using service
        created_tag = await tag_service.create_tag(
            tag_data=tag_data,
            created_by=current_user.id
        )
        
        # Convert to response format
        tag_response = TagResponse(
            _id=str(created_tag["_id"]),
            name=created_tag["name"],
            slug=created_tag["slug"],
            display_name=created_tag.get("display_name"),
            description=created_tag.get("description"),
            category=created_tag["category"],
            color=created_tag["color"],
            parent_tag_id=str(created_tag["parent_tag_id"]) if created_tag.get("parent_tag_id") else None,
            child_tags=[str(cid) for cid in created_tag.get("child_tags", [])],
            status=created_tag["status"],
            is_system_tag=created_tag.get("is_system_tag", False),
            is_auto_assignable=created_tag.get("is_auto_assignable", True),
            usage_count=created_tag.get("usage_count", 0),
            department_ids=[str(did) for did in created_tag.get("department_ids", [])],
            user_ids=[str(uid) for uid in created_tag.get("user_ids", [])],
            created_at=created_tag["created_at"],
            updated_at=created_tag["updated_at"],
            created_by=str(created_tag["created_by"]) if created_tag.get("created_by") else None,
            updated_by=str(created_tag["updated_by"]) if created_tag.get("updated_by") else None
        )
        
        # ===== AUDIT LOGGING =====
        await audit_service.log_tag_created(
            actor_id=str(current_user.id),
            actor_name=current_user.name or current_user.email,
            tag_id=str(created_tag["_id"]),
            tag_name=created_tag["name"],
            tag_category=created_tag["category"],
            correlation_id=correlation_id
        )
        
        logger.info(
            f"✅ [CREATE_TAG] Successfully created tag: {created_tag['name']} (ID: {created_tag['_id']})",
            extra={
                "user_id": str(current_user.id),
                "tag_id": str(created_tag["_id"]),
                "tag_name": created_tag["name"],
                "correlation_id": correlation_id
            }
        )
        
        return tag_response
        
    except ValueError as e:
        logger.warning(
            f"⚠️ [CREATE_TAG] Validation error: {str(e)}",
            extra={
                "user_id": str(current_user.id),
                "tag_name": tag_data.name,
                "error": str(e),
                "correlation_id": correlation_id
            }
        )
        return get_error_response(ErrorCode.VALIDATION_ERROR, str(e))
        
    except HTTPException:
        raise
        
    except Exception as e:
        logger.error(
            f"❌ [CREATE_TAG] Unexpected error: {str(e)}",
            extra={
                "user_id": str(current_user.id),
                "tag_name": tag_data.name,
                "error": str(e),
                "correlation_id": correlation_id
            }
        )
        raise handle_database_error(e, "create_tag", "tag")



