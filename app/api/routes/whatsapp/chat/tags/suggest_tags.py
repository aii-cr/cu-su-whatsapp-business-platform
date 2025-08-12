"""Suggest tags endpoint for autocomplete."""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse

from app.config.error_codes import ErrorCode, get_error_response
from app.core.logger import logger
from app.services.auth import require_permissions
from app.db.models.auth import User
from app.schemas.whatsapp.chat.tag import TagSuggestRequest, TagSuggestResponse, TagSummaryResponse
from app.services import tag_service
from app.core.error_handling import handle_database_error
from app.core.middleware import get_correlation_id

router = APIRouter()

@router.get("/suggest", response_model=TagSuggestResponse)
async def suggest_tags(
    q: str,
    category: str = None,
    limit: int = 10,
    exclude_ids: str = None,
    current_user: User = Depends(require_permissions(["tags:read"]))
):
    """
    Suggest tags for autocomplete based on search query.
    
    Args:
        q: Search query (minimum 1 character)
        category: Filter by tag category (optional)
        limit: Maximum results (1-50, default 10)
        exclude_ids: Comma-separated list of tag IDs to exclude
        current_user: Current authenticated user
        
    Returns:
        List of suggested tags with usage counts
    """
    correlation_id = get_correlation_id()
    
    try:
        logger.info(
            f"🔍 [SUGGEST_TAGS] Suggesting tags for query: {q}",
            extra={
                "user_id": str(current_user.id),
                "query": q,
                "category": category,
                "limit": limit,
                "correlation_id": correlation_id
            }
        )
        
        # Parse exclude_ids
        exclude_id_list = []
        if exclude_ids:
            exclude_id_list = [id.strip() for id in exclude_ids.split(",") if id.strip()]
        
        # Build suggestion request
        suggest_request = TagSuggestRequest(
            query=q,
            category=category,
            limit=limit,
            exclude_ids=exclude_id_list
        )
        
        # Get suggestions from service
        tags, total = await tag_service.suggest_tags(suggest_request)
        
        # Convert to response format
        tag_summaries = []
        for tag in tags:
            tag_summary = TagSummaryResponse(
                _id=str(tag["_id"]),
                name=tag["name"],
                slug=tag["slug"],
                display_name=tag.get("display_name"),
                category=tag["category"],
                color=tag["color"],
                usage_count=tag.get("usage_count", 0)
            )
            tag_summaries.append(tag_summary)
        
        # Build response
        response = TagSuggestResponse(
            tags=tag_summaries,
            total=total,
            query=q
        )
        
        logger.info(
            f"✅ [SUGGEST_TAGS] Found {len(tag_summaries)} suggestions for '{q}' (total: {total})",
            extra={
                "user_id": str(current_user.id),
                "query": q,
                "suggestions_count": len(tag_summaries),
                "total": total,
                "correlation_id": correlation_id
            }
        )
        
        return response
        
    except ValueError as e:
        logger.warning(
            f"⚠️ [SUGGEST_TAGS] Validation error: {str(e)}",
            extra={
                "user_id": str(current_user.id),
                "query": q,
                "error": str(e),
                "correlation_id": correlation_id
            }
        )
        return get_error_response(ErrorCode.VALIDATION_ERROR, str(e))
        
    except HTTPException:
        raise
        
    except Exception as e:
        logger.error(
            f"❌ [SUGGEST_TAGS] Unexpected error: {str(e)}",
            extra={
                "user_id": str(current_user.id),
                "query": q,
                "error": str(e),
                "correlation_id": correlation_id
            }
        )
        raise handle_database_error(e, "suggest_tags", "tags")



