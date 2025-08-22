"""
Conversation summarizer API routes.
Handles conversation summarization requests and responses.
"""

from fastapi import APIRouter, HTTPException, status, Depends
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field

from app.core.logger import logger
from app.services.ai.agents.conversation_summarizer.summarizer_service import summarizer_service
from app.services.ai.agents.conversation_summarizer.schemas import (
    ConversationSummaryRequest,
    ConversationSummaryResponse,
    SummarizationResult
)
from app.schemas import SuccessResponse
from app.core.error_handling import handle_database_error
from app.config.error_codes import get_error_response, ErrorCode

router = APIRouter(prefix="/ai/summarizer", tags=["AI Summarizer"])


class SummarizeRequest(BaseModel):
    """Request to summarize a conversation."""
    conversation_id: str = Field(..., description="Conversation ID to summarize")
    include_metadata: bool = Field(True, description="Whether to include metadata in summary")
    summary_type: str = Field("general", description="Type of summary to generate")


class SummarizeResponse(BaseModel):
    """Response containing conversation summary."""
    success: bool = Field(..., description="Whether summarization was successful")
    summary: Optional[ConversationSummaryResponse] = Field(None, description="Generated summary")
    error: Optional[str] = Field(None, description="Error message if failed")
    processing_time: float = Field(..., description="Time taken to process in seconds")


class CacheStatsResponse(BaseModel):
    """Response containing cache statistics."""
    total_entries: int = Field(..., description="Total cache entries")
    total_size_bytes: int = Field(..., description="Total cache size in bytes")
    cache_ttl_seconds: int = Field(..., description="Cache TTL in seconds")


@router.post("/summarize", response_model=SummarizeResponse)
async def summarize_conversation(request: SummarizeRequest):
    """
    Generate a summary for a conversation.
    Uses AI to analyze and summarize the conversation content.
    """
    try:
        logger.info(f"Generating summary for conversation {request.conversation_id}")
        
        # Create summarization request
        summary_request = ConversationSummaryRequest(
            conversation_id=request.conversation_id,
            include_metadata=request.include_metadata,
            summary_type=request.summary_type
        )
        
        # Generate summary
        result = await summarizer_service.summarize_conversation(summary_request)
        
        if result.success:
            return SummarizeResponse(
                success=True,
                summary=result.summary,
                processing_time=result.processing_time
            )
        else:
            logger.error(f"Summarization failed: {result.error}")
            return SummarizeResponse(
                success=False,
                error=result.error,
                processing_time=result.processing_time
            )
            
    except Exception as e:
        logger.error(f"Error in summarize_conversation: {str(e)}")
        return SummarizeResponse(
            success=False,
            error=f"Error generating summary: {str(e)}",
            processing_time=0.0
        )


@router.get("/health", response_model=Dict[str, Any])
async def get_summarizer_health():
    """
    Get summarizer service health status.
    Checks LLM connection and cache status.
    """
    try:
        logger.info("Performing summarizer health check")
        
        health_data = await summarizer_service.health_check()
        
        return health_data
        
    except Exception as e:
        logger.error(f"Summarizer health check failed: {str(e)}")
        return get_error_response(
            "SUMMARIZER_HEALTH_CHECK_FAILED",
            f"Health check failed: {str(e)}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.get("/cache/stats", response_model=CacheStatsResponse)
async def get_cache_stats():
    """
    Get summarizer cache statistics.
    Returns information about cached summaries.
    """
    try:
        logger.info("Getting summarizer cache statistics")
        
        cache_stats = await summarizer_service.get_cache_stats()
        
        return CacheStatsResponse(**cache_stats)
        
    except Exception as e:
        logger.error(f"Error getting cache stats: {str(e)}")
        return get_error_response(
            ErrorCode.INTERNAL_SERVER_ERROR,
            f"Error getting cache statistics: {str(e)}"
        )


@router.delete("/cache/clear", response_model=SuccessResponse)
async def clear_cache(conversation_id: Optional[str] = None):
    """
    Clear summarizer cache.
    Optionally clear cache for a specific conversation.
    """
    try:
        if conversation_id:
            logger.info(f"Clearing cache for conversation {conversation_id}")
            await summarizer_service.clear_cache(conversation_id)
            message = f"Cache cleared for conversation {conversation_id}"
        else:
            logger.info("Clearing all summarizer cache")
            await summarizer_service.clear_cache()
            message = "All summarizer cache cleared"
        
        return SuccessResponse(
            message=message,
            data={"cleared_conversation": conversation_id}
        )
        
    except Exception as e:
        logger.error(f"Error clearing cache: {str(e)}")
        return get_error_response(
            ErrorCode.INTERNAL_SERVER_ERROR,
            f"Error clearing cache: {str(e)}"
        )


@router.get("/conversations/{conversation_id}/summary", response_model=SummarizeResponse)
async def get_conversation_summary(
    conversation_id: str,
    summary_type: str = "general",
    include_metadata: bool = True
):
    """
    Get summary for a specific conversation.
    Convenience endpoint for getting conversation summaries.
    """
    try:
        logger.info(f"Getting summary for conversation {conversation_id}")
        
        # Create summarization request
        summary_request = ConversationSummaryRequest(
            conversation_id=conversation_id,
            include_metadata=include_metadata,
            summary_type=summary_type
        )
        
        # Generate summary
        result = await summarizer_service.summarize_conversation(summary_request)
        
        if result.success:
            return SummarizeResponse(
                success=True,
                summary=result.summary,
                processing_time=result.processing_time
            )
        else:
            logger.error(f"Failed to get summary: {result.error}")
            return SummarizeResponse(
                success=False,
                error=result.error,
                processing_time=0.0
            )
            
    except Exception as e:
        logger.error(f"Error getting conversation summary: {str(e)}")
        return SummarizeResponse(
            success=False,
            error=f"Error getting summary: {str(e)}",
            processing_time=0.0
        )
