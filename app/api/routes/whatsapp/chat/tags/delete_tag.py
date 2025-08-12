"""Delete tag endpoint."""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse

from app.config.error_codes import ErrorCode, get_error_response
from app.core.logger import logger
from app.services.auth import require_permissions
from app.db.models.auth import User
from app.services import tag_service, audit_service
from app.core.error_handling import handle_database_error
from app.core.middleware import get_correlation_id
from bson import ObjectId

router = APIRouter()

@router.delete("/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tag(
    tag_id: str,
    current_user: User = Depends(require_permissions(["tags:manage"]))
):
    """
    Delete a tag (soft delete by setting status to inactive).
    
    Args:
        tag_id: ID of the tag to delete
        current_user: Current authenticated user
        
    Returns:
        No content (204) on success
    """
    correlation_id = get_correlation_id()
    
    try:
        # Validate tag_id
        try:
            tag_object_id = ObjectId(tag_id)
        except Exception:
            return get_error_response(ErrorCode.INVALID_ID, "Invalid tag ID format")
        
        logger.info(
            f"🗑️ [DELETE_TAG] Deleting tag: {tag_id}",
            extra={
                "user_id": str(current_user.id),
                "tag_id": tag_id,
                "correlation_id": correlation_id
            }
        )
        
        # Get tag for audit logging before deletion
        tag = await tag_service.get_tag(tag_object_id)
        if not tag:
            return get_error_response(ErrorCode.TAG_NOT_FOUND, "Tag not found")
        
        # Delete tag using service
        deleted = await tag_service.delete_tag(
            tag_id=tag_object_id,
            deleted_by=current_user.id
        )
        
        if not deleted:
            return get_error_response(ErrorCode.TAG_NOT_FOUND, "Tag not found")
        
        # ===== AUDIT LOGGING =====
        await audit_service.log_tag_deleted(
            actor_id=str(current_user.id),
            actor_name=current_user.name or current_user.email,
            tag_id=str(tag["_id"]),
            tag_name=tag["name"],
            tag_category=tag["category"],
            correlation_id=correlation_id
        )
        
        logger.info(
            f"✅ [DELETE_TAG] Successfully deleted tag: {tag['name']} (ID: {tag_id})",
            extra={
                "user_id": str(current_user.id),
                "tag_id": tag_id,
                "tag_name": tag["name"],
                "correlation_id": correlation_id
            }
        )
        
        return JSONResponse(
            content={"message": "Tag deleted successfully"},
            status_code=status.HTTP_204_NO_CONTENT
        )
        
    except ValueError as e:
        logger.warning(
            f"⚠️ [DELETE_TAG] Validation error: {str(e)}",
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
            f"❌ [DELETE_TAG] Unexpected error: {str(e)}",
            extra={
                "user_id": str(current_user.id),
                "tag_id": tag_id,
                "error": str(e),
                "correlation_id": correlation_id
            }
        )
        raise handle_database_error(e, "delete_tag", "tag")



