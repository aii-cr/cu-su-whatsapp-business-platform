"""
RAG tool for retrieving and synthesizing information from the knowledge base.
"""

from typing import Any, Dict, List, Optional
from pathlib import Path

from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from app.core.logger import logger
from app.services.ai.config import ai_config
from app.services.ai.tools.base import BaseTool
from app.services.ai.rag.retriever import build_retriever
from app.services.ai.rag.ingest import ingest_documents, check_collection_health


class RAGToolInput(BaseModel):
    """Input schema for the RAG tool."""
    query: str = Field(..., description="User query to search in the knowledge base")
    tenant_id: str = Field(default="default", description="Tenant identifier for filtering")
    locale: str = Field(default="es", description="Language locale for filtering (es/en)")
    max_context_length: int = Field(default=4000, description="Maximum context length in tokens")


class RAGTool(BaseTool):
    """
    RAG tool that retrieves relevant documents and synthesizes responses.
    Handles auto-ingestion if collection is empty.
    """
    
    def __init__(self):
        super().__init__(
            name="rag_search",
            description="Search the knowledge base and generate contextual answers",
            timeout_seconds=15
        )
        
        # Load RAG prompt template
        self.prompt_template = self._load_rag_prompt()
        
        # Initialize LLM
        self.llm = ChatOpenAI(
            openai_api_key=ai_config.openai_api_key,
            model=ai_config.openai_model,
            temperature=0.1,
            max_tokens=ai_config.max_response_length
        )
        
        # Create the RAG chain
        self.rag_chain = self.prompt_template | self.llm
    
    def _load_rag_prompt(self) -> ChatPromptTemplate:
        """Load the RAG prompt template from file."""
        try:
            prompt_path = Path("app/services/ai/prompts/system/rag_answer.md")
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
            ingestion_result = await ingest_documents(
                tenant_id=tool_input.tenant_id,
                locale=tool_input.locale
            )
            
            if not ingestion_result.success:
                return {
                    "answer": "Lo siento, no puedo acceder a la información en este momento. Por favor, contacta con un agente.",
                    "sources": [],
                    "confidence": 0.0,
                    "metadata": {
                        "error": "Knowledge base not available",
                        "ingestion_attempted": True,
                        "ingestion_success": False
                    }
                }
        
        try:
            # Build retriever with filters
            retriever = build_retriever(
                tenant_id=tool_input.tenant_id,
                locale=tool_input.locale,
                k=ai_config.rag_retrieval_k
            )
            
            # Retrieve relevant documents
            retrieval_result = await retriever.get_retrieval_result(tool_input.query)
            
            if not retrieval_result.documents:
                return {
                    "answer": "Lo siento, no encuentro esa información en este momento. ¿Te ayudo con otra cosa o deseas que te contacte un agente?",
                    "sources": [],
                    "confidence": 0.1,
                    "metadata": {
                        "retrieval_time_ms": retrieval_result.retrieval_time_ms,
                        "documents_found": 0
                    }
                }
            
            # Format context from retrieved documents
            context = self._format_context(retrieval_result.documents)
            
            # Generate answer using RAG chain
            response = await self.rag_chain.ainvoke({
                "question": tool_input.query,
                "context": context
            })
            
            answer = response.content.strip()
            
            # Calculate confidence based on retrieval scores and answer length
            confidence = self._calculate_confidence(retrieval_result, answer)
            
            # Prepare sources information
            sources = [
                {
                    "source": doc.source,
                    "section": doc.section,
                    "score": score,
                    "updated_at": doc.updated_at.isoformat()
                }
                for doc, score in zip(retrieval_result.documents, retrieval_result.scores)
            ]
            
            return {
                "answer": answer,
                "sources": sources,
                "confidence": confidence,
                "metadata": {
                    "retrieval_time_ms": retrieval_result.retrieval_time_ms,
                    "documents_found": len(retrieval_result.documents),
                    "context_length": len(context),
                    "query": tool_input.query
                }
            }
            
        except Exception as e:
            logger.error(f"Error in RAG tool execution: {str(e)}")
            return {
                "answer": "Lo siento, ocurrió un error al procesar tu consulta. Por favor, contacta con un agente.",
                "sources": [],
                "confidence": 0.0,
                "metadata": {
                    "error": str(e),
                    "query": tool_input.query
                }
            }
    
    def _format_context(self, documents: List[Any]) -> str:
        """Format retrieved documents into context string."""
        context_parts = []
        
        for doc in documents[:4]:  # Limit to top 4 documents
            # Extract metadata
            source = getattr(doc, 'source', 'unknown')
            section = getattr(doc, 'section', 'general')
            updated_at = getattr(doc, 'updated_at', 'unknown')
            content = getattr(doc, 'content', '')
            
            # Format as specified in prompt
            formatted_doc = f"[{source} | {section} | {updated_at}] {content}"
            context_parts.append(formatted_doc)
        
        return "\n\n".join(context_parts)
    
    def _calculate_confidence(self, retrieval_result: Any, answer: str) -> float:
        """Calculate confidence score based on retrieval and answer quality."""
        if not retrieval_result.documents:
            return 0.0
        
        # Base confidence from retrieval scores
        avg_score = sum(retrieval_result.scores) / len(retrieval_result.scores) if retrieval_result.scores else 0.0
        
        # Adjust based on number of documents found
        doc_bonus = min(0.2, len(retrieval_result.documents) * 0.05)
        
        # Adjust based on answer length (longer answers might be more informative)
        length_bonus = min(0.1, len(answer) / 1000)
        
        # Check if answer indicates uncertainty
        uncertainty_phrases = [
            "no encuentro", "no tengo", "no puedo", "lo siento",
            "don't have", "can't find", "sorry", "not sure"
        ]
        
        if any(phrase in answer.lower() for phrase in uncertainty_phrases):
            uncertainty_penalty = -0.3
        else:
            uncertainty_penalty = 0.0
        
        confidence = avg_score + doc_bonus + length_bonus + uncertainty_penalty
        
        # Clamp between 0.0 and 1.0
        return max(0.0, min(1.0, confidence))
    
    def get_structured_tool(self):
        """Get the StructuredTool version of this tool."""
        return self.to_structured_tool(RAGToolInput)
