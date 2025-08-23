"""
RAG tool for WhatsApp agent - using shared RAG tool with WhatsApp-specific formatting.
"""

from typing import Dict, Any
from pydantic import BaseModel, Field

from app.core.logger import logger
from app.services.ai.shared.rag_tool import retrieve_information
from app.services.ai.shared.rag_config import get_rag_config_for_agent


class RAGToolInput(BaseModel):
    """Input schema for the RAG tool."""
    query: str = Field(..., description="User query to search in the knowledge base")
    tenant_id: str | None = Field(default=None, description="Tenant identifier for filtering (None disables filtering)")
    locale: str | None = Field(default=None, description="Language locale for filtering (None disables filtering)")
    max_context_length: int = Field(default=4000, description="Maximum context length in tokens")


class RAGTool:
    """
    RAG tool that uses the shared RAG tool but formats responses for WhatsApp.
    """
    
    def __init__(self):
        self.name = "rag_tool"
        self.description = "Retrieves relevant information from the knowledge base"
    
    async def execute_with_timeout(self, **kwargs) -> Dict[str, Any]:
        """
        Execute RAG search using the shared RAG tool with WhatsApp formatting.
        
        Args:
            **kwargs: Tool arguments matching RAGToolInput
            
        Returns:
            Dict with answer, sources, and metadata in WhatsApp format
        """
        # Validate input
        tool_input = RAGToolInput(**kwargs)
        
        logger.info(f"🔍 [WHATSAPP_RAG] Executing query: '{tool_input.query[:100]}...'")
        
        try:
            # Get WhatsApp-specific RAG configuration
            rag_config = get_rag_config_for_agent("whatsapp")
            
            # Use the shared RAG tool with WhatsApp configuration
            # Force disable filtering to avoid Qdrant index issues
            result_text = await retrieve_information(
                query=tool_input.query,
                tenant_id=None,  # Force disable filtering
                locale=None,     # Force disable filtering
                k=rag_config["k"]
            )
            
            # Check if we got useful information
            if "No relevant information found" in result_text:
                logger.warning(f"❌ [WHATSAPP_RAG] No information found for query: '{tool_input.query}'")
                return {
                    "status": "success",
                    "data": {
                        "answer": "Lo siento, no encuentro esa información en este momento 🙏. ¿Te ayudo con otra cosa?",
                        "confidence": 0.0,
                        "sources": [],
                        "retrieval_metadata": {
                            "method": "shared_rag",
                            "query": tool_input.query,
                            "result": "no_documents_found"
                        }
                    }
                }
            
            # Simply return the raw result text for LLM processing
            logger.info(f"✅ [WHATSAPP_RAG] Successfully retrieved information for query: '{tool_input.query}'")
            
            return {
                "status": "success",
                "data": {
                    "answer": result_text,  # Raw document content for LLM
                    "confidence": 0.8,  # High confidence since we found documents
                    "sources": [],  # LLM will handle source formatting
                    "retrieval_metadata": {
                        "method": "shared_rag",
                        "query": tool_input.query,
                        "documents_found": result_text.count("--- Document"),
                        "result": "success"
                    }
                }
            }
                
        except Exception as e:
            logger.error(f"❌ [WHATSAPP_RAG] Error in RAG tool execution: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "data": {}
            }
    

    

    

    

