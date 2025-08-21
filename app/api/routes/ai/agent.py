"""
AI agent management API routes.
Handles agent configuration, health checks, and auto-reply toggles.
"""

from fastapi import APIRouter, HTTPException, status, Depends
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field

from app.core.logger import logger
from app.services.ai.agent_service import agent_service
from app.schemas import SuccessResponse
from app.core.error_handling import handle_database_error
from app.config.error_codes import get_error_response

router = APIRouter(prefix="/ai", tags=["AI Agent"])


class AutoReplyToggleRequest(BaseModel):
    """Request to toggle auto-reply for a conversation."""
    conversation_id: str = Field(..., description="Conversation ID")
    enabled: bool = Field(..., description="Whether to enable auto-reply")
    user_id: Optional[str] = Field(None, description="User making the change")


class AgentHealthResponse(BaseModel):
    """AI agent health check response."""
    status: str = Field(..., description="Agent health status")
    agent: Dict[str, Any] = Field(..., description="Agent component health")
    knowledge_base: Dict[str, Any] = Field(..., description="Knowledge base health")
    initialized: bool = Field(..., description="Whether agent is initialized")
    config: Dict[str, Any] = Field(..., description="Agent configuration")
    timestamp: str = Field(..., description="Health check timestamp")


@router.get("/health", response_model=AgentHealthResponse)
async def get_agent_health():
    """
    Get AI agent health status and configuration.
    Checks agent, knowledge base, and dependencies.
    """
    try:
        logger.info("Performing AI agent health check")
        
        health_data = await agent_service.health_check()
        
        return AgentHealthResponse(**health_data)
        
    except Exception as e:
        logger.error(f"AI agent health check failed: {str(e)}")
        return get_error_response(
            "AI_HEALTH_CHECK_FAILED",
            f"Agent health check failed: {str(e)}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.post("/autoreply/toggle", response_model=SuccessResponse)
async def toggle_autoreply(request: AutoReplyToggleRequest):
    """
    Toggle auto-reply for a specific conversation.
    Enables or disables AI automatic responses.
    """
    try:
        logger.info(f"Toggling auto-reply for conversation {request.conversation_id}: {request.enabled}")
        
        result = await agent_service.toggle_autoreply(
            conversation_id=request.conversation_id,
            enabled=request.enabled,
            user_id=request.user_id
        )
        
        if result["success"]:
            return SuccessResponse(
                message=f"Auto-reply {'enabled' if request.enabled else 'disabled'} successfully",
                data={
                    "conversation_id": request.conversation_id,
                    "ai_autoreply_enabled": request.enabled,
                    "changed_by": request.user_id
                }
            )
        else:
            logger.error(f"Failed to toggle auto-reply: {result.get('error', 'Unknown error')}")
            return get_error_response(
                "AUTOREPLY_TOGGLE_FAILED",
                result.get("error", "Failed to toggle auto-reply"),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            
    except Exception as e:
        logger.error(f"Error toggling auto-reply: {str(e)}")
        return get_error_response(
            "AUTOREPLY_TOGGLE_ERROR", 
            f"Error toggling auto-reply: {str(e)}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.post("/conversations/{conversation_id}/process", response_model=SuccessResponse)
async def process_message_manually(
    conversation_id: str,
    user_text: str,
    user_id: Optional[str] = None
):
    """
    Manually trigger AI processing for a message.
    Useful for testing or manual AI responses.
    """
    try:
        logger.info(f"Manual AI processing requested for conversation {conversation_id}")
        
        result = await agent_service.process_whatsapp_message(
            conversation_id=conversation_id,
            message_id="manual_trigger",
            user_text=user_text,
            customer_phone="test",
            ai_autoreply_enabled=True,
            is_first_message=False
        )
        
        return SuccessResponse(
            message="AI processing completed",
            data=result
        )
        
    except Exception as e:
        logger.error(f"Error in manual AI processing: {str(e)}")
        return get_error_response(
            "MANUAL_AI_PROCESSING_FAILED",
            f"Manual AI processing failed: {str(e)}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.post("/knowledge-base/ingest", response_model=SuccessResponse)
async def trigger_knowledge_base_ingestion():
    """
    Manually trigger knowledge base ingestion.
    Useful for updating the RAG database with new content.
    """
    try:
        logger.info("Manual knowledge base ingestion requested")
        
        from app.services.ai.rag.ingest import ingest_documents
        
        result = await ingest_documents()
        
        if result.success:
            return SuccessResponse(
                message="Knowledge base ingestion completed successfully",
                data={
                    "documents_processed": result.documents_processed,
                    "chunks_created": result.chunks_created,
                    "chunks_stored": result.chunks_stored,
                    "processing_time_ms": result.processing_time_ms
                }
            )
        else:
            return get_error_response(
                "KNOWLEDGE_BASE_INGESTION_FAILED",
                f"Ingestion failed: {', '.join(result.errors)}",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            
    except Exception as e:
        logger.error(f"Error in knowledge base ingestion: {str(e)}")
        return get_error_response(
            "KNOWLEDGE_BASE_INGESTION_ERROR",
            f"Knowledge base ingestion error: {str(e)}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
