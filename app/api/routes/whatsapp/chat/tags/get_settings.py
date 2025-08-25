"""Get tag settings endpoint following project patterns."""

from fastapi import APIRouter, Depends

from app.core.logger import logger
from app.db.models.auth import User
from app.schemas.whatsapp.chat.tag import TagSettingsResponse
from app.services.auth import require_permissions
from app.services.whatsapp.tag_service import tag_service
from app.core.error_handling import handle_database_error

router = APIRouter()


@router.get(
    "/settings", 
    response_model=TagSettingsResponse,
    summary="Get tag settings",
    description="Get tag-related settings and configuration limits",
    responses={
        200: {
            "description": "Tag settings retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "max_tags_per_conversation": 10
                    }
                }
            }
        },
        401: {"description": "Authentication required"},
        403: {"description": "Insufficient permissions"},
        500: {"description": "Internal server error"}
    }
)
async def get_tag_settings(
    current_user: User = Depends(require_permissions(["messages:send"]))
):
    """
    Get tag-related settings and configuration limits.
    
    Returns system-wide settings for tag management including:
    - Maximum tags per conversation
    - Other tag-related limits and configurations
    
    **Authentication:**
    Requires 'messages:send' permission.
    """
    logger.info(f"⚙️ [GET_TAG_SETTINGS] Getting tag settings")
    logger.info(f"👤 [GET_TAG_SETTINGS] User: {current_user.email} (ID: {current_user.id})")
    
    try:
        # Get settings using service
        settings = await tag_service.get_tag_settings()
        
        logger.info(f"✅ [GET_TAG_SETTINGS] Retrieved tag settings")
        
        return TagSettingsResponse(**settings)
        
    except Exception as e:
        logger.error(f"❌ [GET_TAG_SETTINGS] Unexpected error: {str(e)}")
        raise handle_database_error(e, "get_tag_settings", "tag")
