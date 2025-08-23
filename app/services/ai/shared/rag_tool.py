"""
Shared RAG tool for all agents.
Uses the same Qdrant collection for consistency across all agents.
"""

from typing import Dict, Any, Optional

from langchain.tools import StructuredTool
from pydantic import BaseModel, Field

from app.core.logger import logger
from app.services.ai.shared.base_tools import BaseAgentTool
from app.services.ai.rag.retriever import build_retriever


class SharedRAGInput(BaseModel):
    """Input schema for shared RAG tool."""
    query: str = Field(..., description="The query to search for relevant information")
    tenant_id: str = Field(default=None, description="Tenant ID for filtering (None disables filtering)")
    locale: str = Field(default=None, description="Language locale (None disables filtering)")
    k: int = Field(default=6, description="Number of documents to retrieve")


class SharedRAGTool(BaseAgentTool):
    """Shared RAG tool for retrieving relevant information for all agents."""
    
    name: str = "retrieve_information"
    description: str = """
    Retrieves relevant information from the knowledge base using RAG (Retrieval-Augmented Generation).
    
    CRITICAL USAGE GUIDELINES:
    - Use this tool when the customer asks for specific information about services, products, policies, procedures, or any topic
    - ALWAYS use the COMPLETE customer message as the query, not just keywords
    - Examples of good queries:
      * "que velocidades de internet tienen?" (not just "internet")
      * "what services do you offer?" (not just "services")
      * "cuáles son los precios?" (not just "precios")
      * "what are your business hours?" (not just "hours")
    
    This tool helps craft better responses by providing accurate, up-to-date information from the knowledge base.
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._retriever = None
    
    async def _get_retriever(self, tenant_id: str = None, locale: str = None, k: int = 6):
        """Get or create retriever instance."""
        if not self._retriever:
            self._retriever = build_retriever(
                tenant_id=tenant_id,  # None disables filtering
                locale=locale,        # None disables filtering
                k=k
            )
        return self._retriever
    
    async def _arun(
        self,
        query: str,
        tenant_id: str = None,
        locale: str = None, 
        k: int = 6,
        run_manager=None
    ) -> str:
        """
        Retrieve relevant information using RAG.
        
        Args:
            query: Search query (should be the complete customer message)
            tenant_id: Tenant identifier
            locale: Language locale
            k: Number of documents to retrieve
            
        Returns:
            Formatted relevant information
        """
        self._log_usage(query=query, tenant_id=tenant_id, locale=locale, k=k)
        
        try:
            # Log the query for debugging
            logger.info(f"🔍 [SHARED_RAG] Query: '{query[:100]}...' (length: {len(query)})")
            
            # Force disable filtering to avoid Qdrant index issues
            tenant_id = None
            locale = None
            
            # Get retriever
            retriever = await self._get_retriever(tenant_id, locale, k)
            
            # Retrieve documents
            result = await retriever.get_retrieval_result(query)
            
            logger.info(f"📊 [SHARED_RAG] Found {result.total_found} documents for query: '{query}'")
            
            if not result.documents:
                logger.warning(f"❌ [SHARED_RAG] No documents found for query: '{query}'")
                return f"No relevant information found for query: '{query}'\n\nSuggestion: Try rephrasing the query or using different keywords."
            
            # Format the results
            formatted_results = []
            formatted_results.append(f"=== RELEVANT INFORMATION FOR: {query} ===")
            formatted_results.append(f"Found {result.total_found} relevant document(s)")
            formatted_results.append("")
            
            for i, doc in enumerate(result.documents, 1):
                formatted_results.append(f"--- Document {i} ---")
                formatted_results.append(f"Source: {doc.source}")
                
                if hasattr(doc, 'section') and doc.section:
                    formatted_results.append(f"Section: {doc.section}")
                
                if hasattr(doc, 'updated_at') and doc.updated_at:
                    formatted_results.append(f"Updated: {doc.updated_at}")
                
                formatted_results.append("")
                formatted_results.append(doc.content)
                formatted_results.append("")
            
            # Add metadata
            formatted_results.append(f"=== RETRIEVAL METADATA ===")
            formatted_results.append(f"Query: {query}")
            formatted_results.append(f"Results found: {result.total_found}")
            formatted_results.append(f"Retrieval time: {result.retrieval_time_ms}ms")
            
            if result.scores:
                avg_score = sum(result.scores) / len(result.scores)
                formatted_results.append(f"Average relevance score: {avg_score:.3f}")
                
                # Add quality indicator
                if avg_score > 0.8:
                    formatted_results.append("Quality: Excellent match")
                elif avg_score > 0.6:
                    formatted_results.append("Quality: Good match")
                else:
                    formatted_results.append("Quality: Moderate match - consider refining query")
            
            result_text = "\n".join(formatted_results)
            
            logger.info(
                f"✅ [SHARED_RAG] Query completed: '{query}' -> {result.total_found} documents "
                f"in {result.retrieval_time_ms}ms"
            )
            
            return result_text
            
        except Exception as e:
            error_msg = f"Error in shared RAG retrieval: {str(e)}"
            logger.error(f"❌ [SHARED_RAG] {error_msg}")
            return error_msg


def create_shared_rag_tool() -> StructuredTool:
    """Create a structured shared RAG tool for use in LangGraph."""
    
    tool = SharedRAGTool()
    
    return StructuredTool(
        name=tool.name,
        description=tool.description,
        func=tool._run,
        coroutine=tool._arun,
        args_schema=SharedRAGInput
    )


# Convenience function for direct usage
async def retrieve_information(
    query: str,
    tenant_id: str = None,
    locale: str = None,
    k: int = 6
) -> str:
    """
    Convenience function to retrieve information directly.
    
    Args:
        query: Search query
        tenant_id: Tenant identifier (ignored - filtering disabled)
        locale: Language locale (ignored - filtering disabled)
        k: Number of documents to retrieve
        
    Returns:
        Formatted relevant information
    """
    tool = SharedRAGTool()
    # Force disable filtering to avoid Qdrant index issues
    return await tool._arun(query=query, tenant_id=None, locale=None, k=k)
