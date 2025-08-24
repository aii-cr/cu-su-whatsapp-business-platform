"""
Writer Agent service for generating contextual responses with helpfulness validation.
"""

from typing import Dict, Any, Optional
from datetime import datetime
import re

from app.core.logger import logger
from app.services.ai.agents.writer.graphs.writer_agent import WriterAgent, WriterAgentState
from app.schemas.ai.writer_response import StructuredWriterResponse, WriterAgentResult


def clean_markdown_to_plain_text(markdown_text: str) -> str:
    """
    Convert markdown text to plain text suitable for WhatsApp.
    
    Args:
        markdown_text: Text that may contain markdown formatting
        
    Returns:
        Plain text without markdown formatting
    """
    if not markdown_text:
        return ""
    
    # Remove bold formatting (**text** -> text)
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', markdown_text)
    
    # Remove italic formatting (*text* -> text)
    text = re.sub(r'\*(.*?)\*', r'\1', text)
    
    # Remove code formatting (`text` -> text)
    text = re.sub(r'`(.*?)`', r'\1', text)
    
    # Remove strikethrough formatting (~~text~~ -> text)
    text = re.sub(r'~~(.*?)~~', r'\1', text)
    
    # Remove header formatting (# text -> text)
    text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)
    
    # Remove link formatting ([text](url) -> text)
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
    
    # Remove image formatting (![alt](url) -> alt)
    text = re.sub(r'!\[([^\]]*)\]\([^)]+\)', r'\1', text)
    
    # Clean up extra whitespace
    text = re.sub(r'\n\s*\n', '\n\n', text)
    text = text.strip()
    
    return text


class WriterAgentService:
    """
    Service wrapper for the Writer Agent.
    Provides high-level interface for generating responses.
    """
    
    def __init__(self):
        """Initialize the Writer Agent service."""
        self.agent = WriterAgent()
        logger.info("Writer Agent service initialized")
    
    def _parse_structured_response(self, raw_response: str) -> Optional[StructuredWriterResponse]:
        """
        Parse structured response from AI output.
        
        Expected format:
        customer_response:
        [actual message content]
        
        reason:
        [reasoning content]
        
        Args:
            raw_response: The raw response from the AI model
            
        Returns:
            StructuredWriterResponse if parsing successful, None otherwise
        """
        try:
            # Use regex to extract customer_response and reason sections
            customer_pattern = r'customer_response:\s*\n(.*?)(?=\n\s*reason:|$)'
            reason_pattern = r'reason:\s*\n(.*?)$'
            
            customer_match = re.search(customer_pattern, raw_response, re.DOTALL | re.IGNORECASE)
            reason_match = re.search(reason_pattern, raw_response, re.DOTALL | re.IGNORECASE)
            
            if customer_match and reason_match:
                customer_response = customer_match.group(1).strip()
                reason = reason_match.group(1).strip()
                
                # Clean markdown from customer response
                customer_response = clean_markdown_to_plain_text(customer_response)
                
                logger.info("Successfully parsed structured response")
                return StructuredWriterResponse(
                    customer_response=customer_response,
                    reason=reason
                )
            else:
                logger.warning("Could not parse structured response - missing sections")
                return None
                
        except Exception as e:
            logger.error(f"Error parsing structured response: {str(e)}")
            return None
    
    async def generate_response(
        self,
        user_query: str,
        conversation_id: Optional[str] = None,
        mode: str = "custom"
    ) -> WriterAgentResult:
        """
        Generate a response using the Writer Agent.
        
        Args:
            user_query: The human agent's request or query
            conversation_id: Optional conversation ID for context
            mode: "prebuilt" for contextual responses, "custom" for agent requests
            
        Returns:
            WriterAgentResult with structured response and metadata
        """
        start_time = datetime.now()
        
        try:
            # Run the Writer Agent
            result: WriterAgentState = await self.agent.generate_response(
                user_query=user_query,
                conversation_id=conversation_id,
                mode=mode
            )
            
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            
            # Check if there was an error in the graph
            if result.get("error"):
                logger.error(f"Writer Agent graph error: {result['error']}")
                return WriterAgentResult(
                    success=False,
                    raw_response="",
                    error="Lo siento, ocurrió un error generando la respuesta. Por favor, inténtalo de nuevo.",
                    metadata={
                        "processing_time_ms": int(processing_time),
                        "conversation_id": conversation_id,
                        "debug_error": result["error"]
                    }
                )
            
            # Extract the final response
            raw_response = result.get("response", "")
            if not raw_response:
                # Fallback: get last non-helpfulness response
                for msg in reversed(result.get("messages", [])):
                    if (msg.get("role") == "assistant" and 
                        not msg.get("tool_calls") and 
                        "HELPFULNESS:" not in msg.get("content", "")):
                        raw_response = msg["content"]
                        break
            
            # Parse structured response
            structured_response = self._parse_structured_response(raw_response)
            
            metadata = {
                "iterations": result.get("iteration_count", 0),
                "helpfulness_score": result.get("helpfulness_score", "unknown"),
                "processing_time_ms": int(processing_time),
                "node_history": result.get("node_history", []),
                "conversation_id": conversation_id,
                "model_used": self.agent.model_name,
                "has_structured_format": structured_response is not None
            }
            
            return WriterAgentResult(
                success=True,
                structured_response=structured_response,
                raw_response=raw_response,
                metadata=metadata
            )
            
        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            error_msg = f"Error generating response: {str(e)}"
            
            logger.error(error_msg)
            
            # Provide user-friendly error message
            user_friendly_error = "Lo siento, ocurrió un error generando la respuesta. Por favor, inténtalo de nuevo."
            
            return WriterAgentResult(
                success=False,
                raw_response="",
                error=user_friendly_error,
                metadata={
                    "processing_time_ms": int(processing_time),
                    "conversation_id": conversation_id,
                    "debug_error": error_msg  # Keep detailed error for debugging
                }
            )
    
    async def generate_contextual_response(self, conversation_id: str) -> WriterAgentResult:
        """
        Generate the best possible response for current conversation context.
        This is a convenience method for the main use case.
        
        Args:
            conversation_id: The conversation ID to analyze
            
        Returns:
            WriterAgentResult with structured response and metadata
        """
        query = (
            "Generate the best possible response for the current conversation context. "
            "CRITICAL: Focus on the customer's LAST message and what they specifically asked for. "
            "Use appropriate tools (RAG for services/info, reservations for bookings, etc.) "
            "to provide helpful, specific answers rather than generic responses. "
            "Address their actual question, not just general conversation flow."
        )
        
        return await self.generate_response(
            user_query=query,
            conversation_id=conversation_id
        )
    
    def _convert_to_legacy_format(self, result: WriterAgentResult) -> Dict[str, Any]:
        """
        Convert new WriterAgentResult to legacy format for backward compatibility.
        
        Args:
            result: The new structured result
            
        Returns:
            Legacy format dictionary
        """
        # Use customer_response if available, otherwise fall back to raw_response
        response_text = ""
        if result.structured_response:
            response_text = result.structured_response.customer_response
        elif result.raw_response:
            response_text = result.raw_response
        
        return {
            "success": result.success,
            "response": response_text,
            "metadata": result.metadata,
            "error": result.error
        }
    
    async def generate_response_legacy(
        self,
        user_query: str,
        conversation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Legacy method that returns old format for backward compatibility.
        Use generate_response() for new structured format.
        """
        result = await self.generate_response(user_query, conversation_id)
        return self._convert_to_legacy_format(result)
    
    async def generate_contextual_response_legacy(self, conversation_id: str) -> Dict[str, Any]:
        """
        Legacy method that returns old format for backward compatibility.
        Use generate_contextual_response() for new structured format.
        """
        result = await self.generate_contextual_response(conversation_id)
        return self._convert_to_legacy_format(result)
    
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
