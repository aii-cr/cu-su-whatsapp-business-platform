"""Delete tag endpoint following project patterns."""

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, status

from app.config.error_codes import ErrorCode
from app.core.logger import logger
from app.core.middleware import get_correlation_id
from app.db.models.auth import User
from app.services import audit_service
from app.services.auth import require_permissions
from app.services.whatsapp.tag_service import tag_service
from app.core.error_handling import handle_database_error

router = APIRouter()


@router.delete("/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tag(
    tag_id: str,
    current_user: User = Depends(require_permissions(["messages:send"]))
):
    """
    Delete a tag (soft delete - sets status to inactive).
    
    Requires 'messages:send' permission.
    """
    logger.info(f"🏷️ [DELETE_TAG] Deleting tag: {tag_id}")
    logger.info(f"👤 [DELETE_TAG] User: {current_user.email} (ID: {current_user.id})")
    
    try:
        # Validate ObjectId
        try:
            tag_object_id = ObjectId(tag_id)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid tag ID format"
            )
        
        # Get tag name before deletion for audit logging
        tag = await tag_service.get_tag(tag_object_id)
        if not tag:
            logger.error(f"❌ [DELETE_TAG] Tag not found: {tag_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tag not found"
            )
        
        # Delete tag using service (soft delete)
        deleted = await tag_service.delete_tag(tag_object_id)
        if not deleted:
            logger.error(f"❌ [DELETE_TAG] Failed to delete tag: {tag_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tag not found"
            )
        
        # Audit logging
        correlation_id = get_correlation_id()
        await audit_service.log_event(
            action="tag_deleted",
            actor_id=str(current_user.id),
            actor_name=current_user.name or current_user.email,
            details=f"Deleted tag: {tag['name']} (ID: {tag_id})",
            correlation_id=correlation_id
        )
        
        logger.info(f"✅ [DELETE_TAG] Successfully deleted tag: {tag['name']}")
        
        # Return 204 No Content
        return None
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ [DELETE_TAG] Unexpected error: {str(e)}")
        raise handle_database_error(e, "delete_tag", "tag")

