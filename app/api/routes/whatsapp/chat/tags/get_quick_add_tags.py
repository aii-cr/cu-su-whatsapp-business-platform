"""Get quick add tags endpoint following project patterns."""

from fastapi import APIRouter, Depends, Query

from app.core.logger import logger
from app.db.models.auth import User
from app.schemas.whatsapp.chat.tag import TagSuggestResponse
from app.services.auth import require_permissions
from app.services.whatsapp.tag_service import tag_service
from app.core.error_handling import handle_database_error

router = APIRouter()


@router.get(
    "/quick-add", 
    response_model=TagSuggestResponse,
    summary="Get quick add tags",
    description="Get most frequently used tags for quick selection",
    responses={
        200: {
            "description": "Quick add tags retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "suggestions": [
                            {
                                "id": "65a1b2c3d4e5f6789abcdef0",
                                "name": "Customer Support",
                                "slug": "customer-support",
                                "display_name": "Customer Support",
                                "category": "department",
                                "color": "#2563eb",
                                "usage_count": 25
                            }
                        ],
                        "total": 1
                    }
                }
            }
        },
        401: {"description": "Authentication required"},
        403: {"description": "Insufficient permissions"},
        500: {"description": "Internal server error"}
    }
)
async def get_quick_add_tags(
    limit: int = Query(default=7, ge=1, le=20, description="Maximum number of quick add tags"),
    current_user: User = Depends(require_permissions(["messages:send"]))
):
    """
    Get most frequently used tags for quick selection.
    
    **Features:**
    - Returns tags sorted by usage count (most used first)
    - Only returns active, auto-assignable tags
    - Configurable limit (default: 7 tags)
    
    **Use Cases:**
    - Quick tag selection in conversation modals
    - Frequently used tags display
    - Tag recommendations based on usage
    
    **Authentication:**
    Requires 'messages:send' permission.
    """
    logger.info(f"⚡ [GET_QUICK_ADD_TAGS] Getting quick add tags: limit={limit}")
    logger.info(f"👤 [GET_QUICK_ADD_TAGS] User: {current_user.email} (ID: {current_user.id})")
    
    try:
        # Get quick add tags using service
        tags = await tag_service.get_quick_add_tags(limit=limit)
        
        # Convert to response format
        suggestions = []
        for tag in tags:
            suggestions.append({
                "id": str(tag["_id"]),
                "name": tag["name"],
                "slug": tag["slug"],
                "display_name": tag.get("display_name"),
                "category": tag["category"],
                "color": tag["color"],
                "usage_count": tag["usage_count"]
            })
        
        logger.info(f"✅ [GET_QUICK_ADD_TAGS] Found {len(suggestions)} quick add tags")
        
        return TagSuggestResponse(
            suggestions=suggestions,
            total=len(suggestions)
        )
        
    except Exception as e:
        logger.error(f"❌ [GET_QUICK_ADD_TAGS] Unexpected error: {str(e)}")
        raise handle_database_error(e, "get_quick_add_tags", "tag")
