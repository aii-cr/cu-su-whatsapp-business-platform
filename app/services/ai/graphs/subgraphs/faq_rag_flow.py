"""
FAQ/RAG flow subgraph.
Retrieves relevant documents and synthesizes answers using the RAG prompt.
"""

from typing import Dict, Any
from app.core.logger import logger
from app.services.ai.tools.rag_tool import RAGTool
from app.services.ai.config import ai_config


async def run_rag_flow(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute the RAG flow for FAQ-type queries.
    
    Args:
        state: Agent state dictionary
        
    Returns:
        Updated state with RAG results
    """
    state["node_history"] = state.get("node_history", []) + ["faq_rag"]
    
    logger.info(f"Running RAG flow for query: '{state['user_text'][:50]}...'")
    
    try:
        # Initialize RAG tool
        rag_tool = RAGTool()
        
        # Execute RAG search
        rag_result = await rag_tool.execute_with_timeout(
            query=state["user_text"],
            tenant_id="default",  # TODO: Extract from conversation metadata
            locale=state.get("customer_language", "es"),
            max_context_length=ai_config.max_context_tokens
        )
        
        if rag_result.status == "success":
            # Extract results
            answer = rag_result.data["answer"]
            confidence = rag_result.data["confidence"]
            sources = rag_result.data["sources"]
            
            # Update state
            state["reply"] = answer
            state["confidence"] = confidence
            state["tool_result"] = rag_result.data
            state["context_docs"] = sources
            
            # Check if we need human handoff based on confidence
            if confidence < ai_config.confidence_threshold:
                state["requires_human_handoff"] = True
                
                # Append handoff message if confidence is very low
                if confidence < 0.3:
                    state["reply"] += "\n\n¿Te gustaría que te conecte con un agente?"
            
            logger.info(
                f"RAG flow completed successfully (confidence: {confidence:.2f}, "
                f"sources: {len(sources)})"
            )
            
        else:
            # Handle RAG tool failure
            logger.error(f"RAG tool failed: {rag_result.error}")
            
            state["reply"] = "Lo siento, no puedo acceder a la información en este momento. Te conectaré con un agente."
            state["confidence"] = 0.0
            state["requires_human_handoff"] = True
            state["tool_result"] = {
                "error": rag_result.error,
                "status": rag_result.status
            }
        
    except Exception as e:
        logger.error(f"Error in RAG flow: {str(e)}")
        
        state["reply"] = "Lo siento, ocurrió un error procesando tu consulta. Un agente te ayudará pronto."
        state["confidence"] = 0.0
        state["requires_human_handoff"] = True
        state["tool_result"] = {"error": str(e)}
    
    return state
