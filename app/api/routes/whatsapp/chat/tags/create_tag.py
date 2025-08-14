"""Create tag endpoint following send_message.py pattern."""

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, status

from app.config.error_codes import ErrorCode
from app.core.logger import logger
from app.core.middleware import get_correlation_id
from app.db.models.auth import User
from app.schemas.whatsapp.chat.tag import TagCreate, TagResponse
from app.services import audit_service
from app.services.auth import require_permissions
from app.services.whatsapp.tag_service import tag_service
from app.core.error_handling import handle_database_error

router = APIRouter()


@router.post("/", response_model=TagResponse, status_code=status.HTTP_201_CREATED)
async def create_tag(
    tag_data: TagCreate,
    current_user: User = Depends(require_permissions(["messages:send"]))
):
    """
    Create a new tag for conversation categorization.
    
    Requires 'messages:send' permission (same as sending messages).
    """
    logger.info(f"🏷️ [CREATE_TAG] Creating tag: {tag_data.name}")
    logger.info(f"👤 [CREATE_TAG] User: {current_user.email} (ID: {current_user.id})")
    
    try:
        # Create tag using service
        tag = await tag_service.create_tag(tag_data, current_user.id)
        
        # Audit logging
        correlation_id = get_correlation_id()
        await audit_service.log_event(
            action="tag_created",
            actor_id=str(current_user.id),
            actor_name=current_user.name or current_user.email,
            details=f"Created tag: {tag_data.name}",
            correlation_id=correlation_id
        )
        
        logger.info(f"✅ [CREATE_TAG] Successfully created tag: {tag['name']} (ID: {tag['_id']})")
        
        return TagResponse(
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
        
    except ValueError as e:
        logger.warning(f"⚠️ [CREATE_TAG] Validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ [CREATE_TAG] Unexpected error: {str(e)}")
        raise handle_database_error(e, "create_tag", "tag")
