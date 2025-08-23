"""
RAG tool for retrieving and synthesizing information from the knowledge base.
Uses the shared hybrid retriever for consistent performance.
"""

from typing import Any, Dict, List, Optional
from pathlib import Path

from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from app.core.logger import logger
from app.services.ai.config import ai_config
from app.services.ai.agents.whatsapp.tools.base import BaseTool
from app.services.ai.rag.retriever import build_retriever
from app.services.ai.rag.ingest import ingest_documents, check_collection_health
from app.services.ai.rag.schemas import RetrievalMethod


class RAGToolInput(BaseModel):
    """Input schema for the RAG tool."""
    query: str = Field(..., description="User query to search in the knowledge base")
    tenant_id: str = Field(default=None, description="Tenant identifier for filtering (None disables filtering)")
    locale: str = Field(default="es_CR", description="Language locale for filtering (es_CR/en_US)")
    max_context_length: int = Field(default=4000, description="Maximum context length in tokens")


class RAGTool(BaseTool):
    """
    RAG tool that retrieves relevant documents and synthesizes responses.
    Handles auto-ingestion if collection is empty.
    Uses the shared hybrid retriever for optimal performance.
    """
    
    def __init__(self):
        super().__init__(
            name="rag_search",
            description="Search the knowledge base and generate contextual answers",
            timeout_seconds=15
        )
        
        # Load RAG prompt template
        self._prompt_template = self._load_rag_prompt()
        
        # Initialize LLM
        self._llm = ChatOpenAI(
            openai_api_key=ai_config.openai_api_key,
            model=ai_config.openai_model,
            temperature=0.1,
            max_tokens=ai_config.max_response_length
        )
        
        # Create the RAG chain
        self._rag_chain = self._prompt_template | self._llm
    
    def _load_rag_prompt(self) -> ChatPromptTemplate:
        """Load the RAG prompt template from file."""
        try:
            prompt_path = Path("app/services/ai/agents/whatsapp/prompts/system/rag_answer.md")
            prompt_content = prompt_path.read_text(encoding="utf-8")
            
            return ChatPromptTemplate.from_template(prompt_content)
            
        except Exception as e:
            logger.error(f"Error loading RAG prompt: {str(e)}")
            # Fallback to inline prompt
            fallback_prompt = """
            You are a helpful assistant. Answer the user's question using only the provided context.
            
            Context: {context}
            Question: {question}
            
            If you cannot answer based on the context, say you don't have that information.
            """
            return ChatPromptTemplate.from_template(fallback_prompt)
    
    async def _execute(self, **kwargs) -> Dict[str, Any]:
        """
        Execute RAG search and synthesis.
        
        Args:
            **kwargs: Tool arguments matching RAGToolInput
            
        Returns:
            Dict with answer, sources, and metadata
        """
        # Validate input
        tool_input = RAGToolInput(**kwargs)
        
        logger.info(f"RAG tool executing query: '{tool_input.query[:100]}...'")
        
        # Check collection health first
        collection_health = await check_collection_health()
        
        # Auto-ingest if collection is empty or doesn't exist
        if not collection_health.get("collection_exists", False) or \
           collection_health.get("vectors_count", 0) == 0:
            
            logger.info("Collection empty or missing, triggering auto-ingestion")
            ingestion_result = await ingest_documents()
            
            if not ingestion_result.success:
                return {
                    "status": "error",
                    "error": f"Failed to ingest documents: {ingestion_result.errors}",
                    "data": {}
                }
        
        try:
            # Execute retrieval using the shared hybrid retriever
            result = await self._execute_retrieval(tool_input)
            return result
            
        except Exception as e:
            logger.error(f"Error in RAG tool execution: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "data": {}
            }
    
    async def _execute_retrieval(self, tool_input: RAGToolInput) -> Dict[str, Any]:
        """Execute retrieval using the shared hybrid retriever."""
        try:
            # Build hybrid retriever with optimal settings
            retriever = build_retriever(
                tenant_id=tool_input.tenant_id,
                locale=tool_input.locale,
                k=10,
                score_threshold=0.20,
                method=RetrievalMethod.DENSE,
                enable_multi_query=True,
                enable_compression=True
            )
            
            # Retrieve documents
            retrieval_result = await retriever.get_retrieval_result(tool_input.query)
            
            if not retrieval_result.documents:
                return {
                    "status": "success",
                    "data": {
                        "answer": "Lo siento, no encuentro esa información en este momento 🙏. ¿Te ayudo con otra cosa?",
                        "confidence": 0.0,
                        "sources": [],
                        "retrieval_metadata": {
                            "method": retrieval_result.method,
                            "expanded_queries": retrieval_result.expanded_queries,
                            "filters_applied": retrieval_result.filters_applied,
                            "threshold_used": retrieval_result.threshold_used,
                            "metadata_overrides": retrieval_result.metadata_overrides
                        }
                    }
                }
            
            # Format context for RAG prompt
            context = self._format_context_for_rag(retrieval_result.documents)
            
            # Generate answer
            answer = await self._generate_answer(tool_input.query, context)
            
            # Calculate confidence
            confidence = self._calculate_confidence(retrieval_result.scores)
            
            # Format sources
            sources = [
                {
                    "content": doc.content,
                    "source": doc.source,
                    "section": doc.section,
                    "subsection": doc.subsection,
                    "title": doc.title,
                    "tags": doc.tags,
                    "price_text": doc.price_text,
                    "url": doc.url,
                    "contact_value": doc.contact_value,
                    "score": score
                }
                for doc, score in zip(retrieval_result.documents, retrieval_result.scores)
            ]
            
            return {
                "status": "success",
                "data": {
                    "answer": answer,
                    "confidence": confidence,
                    "sources": sources,
                    "retrieval_metadata": {
                        "method": retrieval_result.method,
                        "expanded_queries": retrieval_result.expanded_queries,
                        "filters_applied": retrieval_result.filters_applied,
                        "threshold_used": retrieval_result.threshold_used,
                        "metadata_overrides": retrieval_result.metadata_overrides,
                        "retrieval_time_ms": retrieval_result.retrieval_time_ms
                    }
                }
            }
            
        except Exception as e:
            logger.error(f"Error in retrieval: {str(e)}")
            raise
    
    def _format_context_for_rag(self, documents) -> str:
        """Format retrieved documents for RAG prompt."""
        context_parts = []
        
        for doc in documents:
            # Format each document with metadata
            meta_info = f"[{doc.source} | {doc.section}"
            if doc.subsection:
                meta_info += f" > {doc.subsection}"
            if doc.updated_at:
                meta_info += f" | {doc.updated_at.strftime('%Y-%m-%d')}"
            meta_info += "]"
            
            context_parts.append(f"{meta_info}\n{doc.content}")
        
        return "\n\n".join(context_parts)
    
    async def _generate_answer(self, query: str, context: str) -> str:
        """Generate answer using RAG prompt."""
        try:
            result = await self._rag_chain.ainvoke({
                "question": query,
                "context": context
            })
            
            return result.content.strip()
            
        except Exception as e:
            logger.error(f"Error generating answer: {str(e)}")
            return "Lo siento, no puedo generar una respuesta en este momento."
    
    def _calculate_confidence(self, scores: list) -> float:
        """Calculate confidence based on retrieval scores."""
        if not scores:
            return 0.0
        
        # Use the highest score as base confidence
        max_score = max(scores)
        
        # Boost confidence if we have multiple high-scoring results
        high_score_count = sum(1 for score in scores if score > 0.7)
        if high_score_count > 1:
            max_score = min(1.0, max_score + 0.1)
        
        return max_score
    

