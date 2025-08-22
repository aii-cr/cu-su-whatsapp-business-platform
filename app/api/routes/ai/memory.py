"""
AI Memory Management API endpoints.
Provides access to conversation memory and context management.
"""

from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from app.services.auth import require_permissions
from app.db.models.auth import User
from app.core.logger import logger
from app.services.ai.agents.whatsapp.agent_service import agent_service

router = APIRouter(prefix="/ai/memory", tags=["AI Memory"])


@router.get("/conversation/{conversation_id}/context")
async def get_conversation_context(
    conversation_id: str,
    current_user: Dict[str, Any] = Depends(require_permissions(["conversations:read"]))
) -> Dict[str, Any]:
    """
    Get conversation context and memory information.
    
    Args:
        conversation_id: Conversation identifier
        current_user: Authenticated user
        
    Returns:
        Conversation context information
    """
    try:
        context = await agent_service.get_conversation_context(conversation_id)
        
        if "error" in context:
            raise HTTPException(status_code=500, detail=context["error"])
        
        return {
            "success": True,
            "conversation_id": conversation_id,
            "context": context
        }
        
    except Exception as e:
        logger.error(f"Error getting conversation context: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/conversation/{conversation_id}/memory")
async def clear_conversation_memory(
    conversation_id: str,
    current_user: Dict[str, Any] = Depends(require_permissions(["conversations:write"]))
) -> Dict[str, Any]:
    """
    Clear conversation memory and session data.
    
    Args:
        conversation_id: Conversation identifier
        current_user: Authenticated user
        
    Returns:
        Result of the clear operation
    """
    try:
        result = await agent_service.clear_conversation_memory(conversation_id)
        
        if not result.get("success", False):
            raise HTTPException(status_code=500, detail=result.get("error", "Unknown error"))
        
        return result
        
    except Exception as e:
        logger.error(f"Error clearing conversation memory: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/statistics")
async def get_memory_statistics(
    current_user: Dict[str, Any] = Depends(require_permissions(["admin:read"]))
) -> Dict[str, Any]:
    """
    Get memory service statistics.
    
    Args:
        current_user: Authenticated user with admin permissions
        
    Returns:
        Memory statistics
    """
    try:
        stats = await agent_service.get_memory_statistics()
        
        if "error" in stats:
            raise HTTPException(status_code=500, detail=stats["error"])
        
        return {
            "success": True,
            "statistics": stats
        }
        
    except Exception as e:
        logger.error(f"Error getting memory statistics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def get_memory_health(
    current_user: Dict[str, Any] = Depends(require_permissions(["admin:read"]))
) -> Dict[str, Any]:
    """
    Get memory service health information.
    
    Args:
        current_user: Authenticated user with admin permissions
        
    Returns:
        Memory service health status
    """
    try:
        health = await agent_service.health_check()
        
        return {
            "success": True,
            "memory_service": health.get("memory_service", {}),
            "status": health.get("status", "unknown")
        }
        
    except Exception as e:
        logger.error(f"Error getting memory health: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
