"""Update tag endpoint."""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse

from app.config.error_codes import ErrorCode, get_error_response
from app.core.logger import logger
from app.services.auth import require_permissions
from app.db.models.auth import User
from app.schemas.whatsapp.chat.tag import TagUpdate, TagResponse
from app.services import tag_service, audit_service
from app.core.error_handling import handle_database_error
from app.core.middleware import get_correlation_id
from bson import ObjectId

router = APIRouter()

@router.put("/{tag_id}", response_model=TagResponse)
async def update_tag(
    tag_id: str,
    tag_data: TagUpdate,
    current_user: User = Depends(require_permissions(["tags:write"]))
):
    """
    Update an existing tag.
    
    Args:
        tag_id: ID of the tag to update
        tag_data: Tag update data
        current_user: Current authenticated user
        
    Returns:
        Updated tag details
    """
    correlation_id = get_correlation_id()
    
    try:
        # Validate tag_id
        try:
            tag_object_id = ObjectId(tag_id)
        except Exception:
            return get_error_response(ErrorCode.INVALID_ID, "Invalid tag ID format")
        
        logger.info(
            f"✏️ [UPDATE_TAG] Updating tag: {tag_id}",
            extra={
                "user_id": str(current_user.id),
                "tag_id": tag_id,
                "correlation_id": correlation_id
            }
        )
        
        # Get original tag for audit logging
        original_tag = await tag_service.get_tag(tag_object_id)
        if not original_tag:
            return get_error_response(ErrorCode.TAG_NOT_FOUND, "Tag not found")
        
        # Update tag using service
        updated_tag = await tag_service.update_tag(
            tag_id=tag_object_id,
            tag_data=tag_data,
            updated_by=current_user.id
        )
        
        if not updated_tag:
            return get_error_response(ErrorCode.TAG_NOT_FOUND, "Tag not found")
        
        # Convert to response format
        tag_response = TagResponse(
            _id=str(updated_tag["_id"]),
            name=updated_tag["name"],
            slug=updated_tag["slug"],
            display_name=updated_tag.get("display_name"),
            description=updated_tag.get("description"),
            category=updated_tag["category"],
            color=updated_tag["color"],
            parent_tag_id=str(updated_tag["parent_tag_id"]) if updated_tag.get("parent_tag_id") else None,
            child_tags=[str(cid) for cid in updated_tag.get("child_tags", [])],
            status=updated_tag["status"],
            is_system_tag=updated_tag.get("is_system_tag", False),
            is_auto_assignable=updated_tag.get("is_auto_assignable", True),
            usage_count=updated_tag.get("usage_count", 0),
            department_ids=[str(did) for did in updated_tag.get("department_ids", [])],
            user_ids=[str(uid) for uid in updated_tag.get("user_ids", [])],
            created_at=updated_tag["created_at"],
            updated_at=updated_tag["updated_at"],
            created_by=str(updated_tag["created_by"]) if updated_tag.get("created_by") else None,
            updated_by=str(updated_tag["updated_by"]) if updated_tag.get("updated_by") else None
        )
        
        # ===== AUDIT LOGGING =====
        # Build changes tracking
        changes = {}
        for field in ["name", "category", "status", "description"]:
            old_value = original_tag.get(field)
            new_value = getattr(tag_data, field, None)
            if new_value is not None and new_value != old_value:
                changes[field] = {"from": old_value, "to": new_value}
        
        await audit_service.log_tag_updated(
            actor_id=str(current_user.id),
            actor_name=current_user.name or current_user.email,
            tag_id=str(updated_tag["_id"]),
            tag_name=updated_tag["name"],
            changes=changes,
            correlation_id=correlation_id
        )
        
        logger.info(
            f"✅ [UPDATE_TAG] Successfully updated tag: {updated_tag['name']} (ID: {tag_id})",
            extra={
                "user_id": str(current_user.id),
                "tag_id": tag_id,
                "tag_name": updated_tag["name"],
                "changes": list(changes.keys()),
                "correlation_id": correlation_id
            }
        )
        
        return tag_response
        
    except ValueError as e:
        logger.warning(
            f"⚠️ [UPDATE_TAG] Validation error: {str(e)}",
            extra={
                "user_id": str(current_user.id),
                "tag_id": tag_id,
                "error": str(e),
                "correlation_id": correlation_id
            }
        )
        return get_error_response(ErrorCode.VALIDATION_ERROR, str(e))
        
    except HTTPException:
        raise
        
    except Exception as e:
        logger.error(
            f"❌ [UPDATE_TAG] Unexpected error: {str(e)}",
            extra={
                "user_id": str(current_user.id),
                "tag_id": tag_id,
                "error": str(e),
                "correlation_id": correlation_id
            }
        )
        raise handle_database_error(e, "update_tag", "tag")



