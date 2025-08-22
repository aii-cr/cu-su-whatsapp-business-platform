"""
Writer Agent API endpoints.
"""

from typing import Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

from app.core.logger import logger
from app.services.auth.utils.session_auth import get_current_user
from app.services.ai.agents.writer.agent_service import writer_agent_service
from app.config.error_codes import get_error_response
from app.schemas.ai.writer_response import StructuredWriterResponse, WriterAgentResult

router = APIRouter()


class WriterQueryRequest(BaseModel):
    """Request model for Writer Agent queries."""
    query: str = Field(..., description="The query or request for the Writer Agent")
    conversation_id: Optional[str] = Field(None, description="Optional conversation ID for context")


class ContextualResponseRequest(BaseModel):
    """Request model for contextual response generation."""
    conversation_id: str = Field(..., description="Conversation ID to analyze for context")


class WriterResponse(BaseModel):
    """Response model for Writer Agent results."""
    success: bool = Field(..., description="Whether the operation was successful")
    response: str = Field(..., description="The generated response")
    metadata: dict = Field(..., description="Additional metadata about the generation")
    error: Optional[str] = Field(None, description="Error message if failed")


@router.post("/generate", response_model=WriterResponse)
async def generate_response(
    request: WriterQueryRequest,
    current_user=Depends(get_current_user)
):
    """
    Generate a response using the Writer Agent.
    
    The Writer Agent will analyze the query, use available tools to gather
    relevant information, and generate a well-crafted response with
    helpfulness validation.
    """
    try:
        logger.info(
            f"Writer Agent request from user {current_user.id}: "
            f"'{request.query[:100]}...' for conversation {request.conversation_id}"
        )
        
        # Generate response (using legacy method for now to maintain compatibility)
        result = await writer_agent_service.generate_response_legacy(
            user_query=request.query,
            conversation_id=request.conversation_id
        )
        
        # Log the result
        if result["success"]:
            logger.info(
                f"Writer Agent response generated successfully "
                f"(iterations: {result['metadata'].get('iterations', 0)}, "
                f"time: {result['metadata'].get('processing_time_ms', 0)}ms)"
            )
        else:
            logger.warning(f"Writer Agent failed: {result.get('error', 'unknown error')}")
        
        return WriterResponse(**result)
        
    except Exception as e:
        logger.error(f"Error in Writer Agent generate endpoint: {str(e)}")
        # Log the detailed error for debugging
        logger.error(f"Writer Agent error details: {str(e)}")
        
        # Return user-friendly error message
        return WriterResponse(
            success=False,
            response="",
            metadata={},
            error="There was an error connecting to the Writer Agent. Please try again or contact IT if the issue persists."
        )


@router.post("/contextual", response_model=WriterResponse)
async def generate_contextual_response(
    request: ContextualResponseRequest,
    current_user=Depends(get_current_user)
):
    """
    Generate the best possible response for current conversation context.
    
    This endpoint analyzes the conversation history and generates an appropriate
    response that continues the conversation naturally based on the context.
    """
    try:
        logger.info(
            f"Contextual response request from user {current_user.id} "
            f"for conversation {request.conversation_id}"
        )
        
        # Generate contextual response (using legacy method for now to maintain compatibility)
        result = await writer_agent_service.generate_contextual_response_legacy(
            conversation_id=request.conversation_id
        )
        
        # Log the result
        if result["success"]:
            logger.info(
                f"Contextual response generated successfully "
                f"(iterations: {result['metadata'].get('iterations', 0)}, "
                f"time: {result['metadata'].get('processing_time_ms', 0)}ms)"
            )
        else:
            logger.warning(f"Contextual response failed: {result.get('error', 'unknown error')}")
        
        return WriterResponse(**result)
        
    except Exception as e:
        logger.error(f"Error in Writer Agent contextual endpoint: {str(e)}")
        # Log the detailed error for debugging
        logger.error(f"Contextual response error details: {str(e)}")
        
        # Return user-friendly error message
        return WriterResponse(
            success=False,
            response="",
            metadata={},
            error="There was an error generating the contextual response. Please try again or contact IT if the issue persists."
        )


@router.post("/generate-structured", response_model=WriterAgentResult)
async def generate_structured_response(
    request: WriterQueryRequest,
    current_user=Depends(get_current_user)
):
    """
    Generate a structured response using the Writer Agent.
    
    Returns the response in a structured format with separate customer_response 
    and reason sections for better UI integration.
    """
    try:
        logger.info(
            f"Structured Writer Agent request from user {current_user.id}: "
            f"'{request.query[:100]}...' for conversation {request.conversation_id}"
        )
        
        # Generate structured response
        result = await writer_agent_service.generate_response(
            user_query=request.query,
            conversation_id=request.conversation_id
        )
        
        # Log the result
        if result.success:
            has_structured = result.structured_response is not None
            logger.info(
                f"Structured Writer Agent response generated successfully "
                f"(structured: {has_structured}, iterations: {result.metadata.get('iterations', 0)}, "
                f"time: {result.metadata.get('processing_time_ms', 0)}ms)"
            )
        else:
            logger.warning(f"Structured Writer Agent failed: {result.error}")
        
        return result
        
    except Exception as e:
        logger.error(f"Error in Writer Agent structured generate endpoint: {str(e)}")
        
        # Return structured error response
        return WriterAgentResult(
            success=False,
            raw_response="",
            error="There was an error connecting to the Writer Agent. Please try again or contact IT if the issue persists.",
            metadata={}
        )


@router.post("/contextual-structured", response_model=WriterAgentResult)
async def generate_structured_contextual_response(
    request: ContextualResponseRequest,
    current_user=Depends(get_current_user)
):
    """
    Generate a structured contextual response for current conversation context.
    
    Returns the response in a structured format with separate customer_response 
    and reason sections for better UI integration.
    """
    try:
        logger.info(
            f"Structured contextual response request from user {current_user.id} "
            f"for conversation {request.conversation_id}"
        )
        
        # Generate structured contextual response
        result = await writer_agent_service.generate_contextual_response(
            conversation_id=request.conversation_id
        )
        
        # Log the result
        if result.success:
            has_structured = result.structured_response is not None
            logger.info(
                f"Structured contextual response generated successfully "
                f"(structured: {has_structured}, iterations: {result.metadata.get('iterations', 0)}, "
                f"time: {result.metadata.get('processing_time_ms', 0)}ms)"
            )
        else:
            logger.warning(f"Structured contextual response failed: {result.error}")
        
        return result
        
    except Exception as e:
        logger.error(f"Error in Writer Agent structured contextual endpoint: {str(e)}")
        
        # Return structured error response
        return WriterAgentResult(
            success=False,
            raw_response="",
            error="There was an error generating the contextual response. Please try again or contact IT if the issue persists.",
            metadata={}
        )


@router.get("/health")
async def health_check():
    """
    Check Writer Agent service health.
    """
    try:
        health_status = await writer_agent_service.health_check()
        
        if health_status.get("status") == "healthy":
            return health_status
        else:
            raise HTTPException(status_code=503, detail=health_status)
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Writer Agent health check failed: {str(e)}")
        raise HTTPException(
            status_code=503,
            detail={"error": "Writer Agent service unavailable", "details": str(e)}
        )
