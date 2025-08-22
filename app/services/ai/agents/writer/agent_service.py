"""
Writer Agent service for generating contextual responses with helpfulness validation.
"""

from typing import Dict, Any, Optional
from datetime import datetime

from app.core.logger import logger
from app.services.ai.agents.writer.graphs.writer_agent import WriterAgent, WriterAgentState


class WriterAgentService:
    """
    Service wrapper for the Writer Agent.
    Provides high-level interface for generating responses.
    """
    
    def __init__(self):
        """Initialize the Writer Agent service."""
        self.agent = WriterAgent()
        logger.info("Writer Agent service initialized")
    
    async def generate_response(
        self,
        user_query: str,
        conversation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate a response using the Writer Agent.
        
        Args:
            user_query: The human agent's request or query
            conversation_id: Optional conversation ID for context
            
        Returns:
            Dictionary with response and metadata
        """
        start_time = datetime.now()
        
        try:
            # Run the Writer Agent
            result: WriterAgentState = await self.agent.generate_response(
                user_query=user_query,
                conversation_id=conversation_id
            )
            
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            
            # Extract the final response
            response = result.get("response", "")
            if not response:
                # Fallback: get last non-helpfulness response
                for msg in reversed(result.get("messages", [])):
                    if (msg.get("role") == "assistant" and 
                        not msg.get("tool_calls") and 
                        "HELPFULNESS:" not in msg.get("content", "")):
                        response = msg["content"]
                        break
            
            return {
                "success": True,
                "response": response,
                "metadata": {
                    "iterations": result.get("iteration_count", 0),
                    "helpfulness_score": result.get("helpfulness_score", "unknown"),
                    "processing_time_ms": int(processing_time),
                    "node_history": result.get("node_history", []),
                    "conversation_id": conversation_id,
                    "model_used": self.agent.model_name
                }
            }
            
        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            error_msg = f"Error generating response: {str(e)}"
            
            logger.error(error_msg)
            
            return {
                "success": False,
                "error": error_msg,
                "response": "Lo siento, ocurrió un error generando la respuesta.",
                "metadata": {
                    "processing_time_ms": int(processing_time),
                    "conversation_id": conversation_id
                }
            }
    
    async def generate_contextual_response(self, conversation_id: str) -> Dict[str, Any]:
        """
        Generate the best possible response for current conversation context.
        This is a convenience method for the main use case.
        
        Args:
            conversation_id: The conversation ID to analyze
            
        Returns:
            Dictionary with response and metadata
        """
        query = (
            "Generate the best possible response for the current conversation context. "
            "Analyze the conversation history, understand what the customer needs, "
            "and craft an appropriate response that continues the conversation naturally."
        )
        
        return await self.generate_response(
            user_query=query,
            conversation_id=conversation_id
        )
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Check the health status of the Writer Agent service.
        
        Returns:
            Health status dictionary
        """
        try:
            # Check agent health
            agent_health = await self.agent.health_check()
            
            return {
                "service": "WriterAgentService",
                "status": agent_health.get("status", "unknown"),
                "agent_health": agent_health,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Writer Agent service health check failed: {str(e)}")
            return {
                "service": "WriterAgentService",
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }


# Global service instance
writer_agent_service = WriterAgentService()
