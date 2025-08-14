"""Tag suggestions endpoint following project patterns."""

from typing import Optional, List
from bson import ObjectId
from fastapi import APIRouter, Depends, Query, HTTPException, status

from app.core.logger import logger
from app.db.models.auth import User
from app.schemas.whatsapp.chat.tag import TagSuggestResponse, TagSummary
from app.services.auth import require_permissions
from app.services.whatsapp.tag_service import tag_service
from app.core.error_handling import handle_database_error

router = APIRouter()


@router.get(
    "/suggest", 
    response_model=TagSuggestResponse,
    summary="Get tag suggestions",
    description="Get tag suggestions for autocomplete with search and filtering capabilities",
    responses={
        200: {
            "description": "Successful response with tag suggestions",
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
        400: {"description": "Bad request - invalid parameters"},
        401: {"description": "Authentication required"},
        403: {"description": "Insufficient permissions"},
        500: {"description": "Internal server error"}
    }
)
async def suggest_tags(
    q: str = Query("", description="Search query (empty returns popular tags)", max_length=100),
    limit: int = Query(default=10, ge=1, le=50, description="Maximum number of suggestions"),
    category: Optional[str] = Query(default=None, description="Filter by tag category"),
    exclude_ids: Optional[str] = Query(default=None, description="Comma-separated tag IDs to exclude"),
    current_user: User = Depends(require_permissions(["messages:send"]))
):
    """
    Get tag suggestions for autocomplete functionality.
    
    **Features:**
    - Empty query returns most popular tags
    - Non-empty query searches by name (case-insensitive)
    - Excludes inactive tags automatically
    - Supports category filtering
    - Excludes specified tag IDs
    
    **Use Cases:**
    - Autocomplete in tag input fields
    - Popular tags display
    - Tag recommendations
    
    **Authentication:**
    Requires 'messages:send' permission.
    """
    logger.info(f"🔍 [SUGGEST_TAGS] Getting suggestions: query='{q}', limit={limit}")
    logger.info(f"👤 [SUGGEST_TAGS] User: {current_user.email} (ID: {current_user.id})")
    
    try:
        # Parse exclude_ids
        exclude_object_ids = []
        if exclude_ids:
            try:
                exclude_object_ids = [ObjectId(tag_id.strip()) for tag_id in exclude_ids.split(",") if tag_id.strip()]
            except Exception:
                # Ignore invalid IDs
                pass
        
        # Get suggestions using service
        tags = await tag_service.suggest_tags(
            query=q,
            limit=limit,
            category=category,
            exclude_ids=exclude_object_ids
        )
        
        # Convert to response format
        suggestions = []
        for tag in tags:
            suggestions.append(TagSummary(
                id=str(tag["_id"]),
                name=tag["name"],
                slug=tag["slug"],
                display_name=tag.get("display_name"),
                category=tag["category"],
                color=tag["color"],
                usage_count=tag["usage_count"]
            ))
        
        logger.info(f"✅ [SUGGEST_TAGS] Found {len(suggestions)} suggestions")
        
        return TagSuggestResponse(
            suggestions=suggestions,
            total=len(suggestions)
        )
        
    except Exception as e:
        logger.error(f"❌ [SUGGEST_TAGS] Unexpected error: {str(e)}")
        raise handle_database_error(e, "suggest_tags", "tag")
