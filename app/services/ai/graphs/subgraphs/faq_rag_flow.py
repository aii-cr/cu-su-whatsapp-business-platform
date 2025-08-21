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
        # Send activity notification for RAG search
        try:
            from app.services import websocket_service
            await websocket_service.notify_ai_agent_activity(
                conversation_id=state["conversation_id"],
                activity_type="rag_search",
                activity_description="Using internal knowledge"
            )
        except Exception as e:
            logger.warning(f"Failed to send RAG activity notification: {str(e)}")
        
        # Initialize RAG tool
        rag_tool = RAGTool()
        
        # Enhance query with conversation context
        enhanced_query = _enhance_query_with_context(
            state["user_text"], 
            state.get("conversation_history", []),
            state.get("conversation_summary", "")
        )
        
        logger.info(f"Enhanced query: '{enhanced_query[:100]}...'")
        
        # Execute RAG search with enhanced query
        rag_result = await rag_tool.execute_with_timeout(
            query=enhanced_query,
            tenant_id="default",  # TODO: Extract from conversation metadata
            locale=state.get("customer_language", "es"),
            max_context_length=ai_config.max_context_tokens
        )
        
        if rag_result.status == "success":
            # Send activity notification for response generation
            try:
                from app.services import websocket_service
                await websocket_service.notify_ai_agent_activity(
                    conversation_id=state["conversation_id"],
                    activity_type="response_generation",
                    activity_description="Generating response"
                )
            except Exception as e:
                logger.warning(f"Failed to send response generation activity notification: {str(e)}")
            
            # Extract results
            answer = rag_result.data["answer"]
            confidence = rag_result.data["confidence"]
            sources = rag_result.data["sources"]
            
            # Post-process answer based on conversation context
            processed_answer = _post_process_answer(
                answer, 
                state.get("conversation_history", []),
                state.get("intent", "faq")
            )
            
            # Update state
            state["reply"] = processed_answer
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


def _enhance_query_with_context(
    user_text: str, 
    conversation_history: list, 
    conversation_summary: str
) -> str:
    """
    Enhance the user query with conversation context.
    
    Args:
        user_text: Current user message
        conversation_history: Previous conversation messages
        conversation_summary: Summary of conversation so far
        
    Returns:
        Enhanced query with context
    """
    enhanced_parts = [user_text]
    
    # Add conversation summary if available
    if conversation_summary:
        enhanced_parts.append(f"Contexto de la conversación: {conversation_summary}")
    
    # Add recent user messages for context (last 2)
    recent_user_messages = [
        msg["content"] for msg in conversation_history[-4:] 
        if msg.get("role") == "user"
    ][-2:]  # Last 2 user messages
    
    if recent_user_messages:
        context_messages = "; ".join(recent_user_messages)
        enhanced_parts.append(f"Mensajes recientes del usuario: {context_messages}")
    
    return " | ".join(enhanced_parts)


def _post_process_answer(
    answer: str, 
    conversation_history: list, 
    intent: str
) -> str:
    """
    Post-process the RAG answer based on conversation context.
    
    Args:
        answer: Raw RAG answer
        conversation_history: Previous conversation messages
        intent: Current intent
        
    Returns:
        Processed answer
    """
    # Remove redundant information if already mentioned
    if conversation_history:
        recent_ai_messages = [
            msg["content"] for msg in conversation_history[-4:] 
            if msg.get("role") == "assistant"
        ]
        
        # Check if we're repeating information
        for recent_msg in recent_ai_messages:
            # Simple check for significant overlap
            recent_words = set(recent_msg.lower().split())
            answer_words = set(answer.lower().split())
            
            if len(recent_words.intersection(answer_words)) > len(answer_words) * 0.7:
                # High overlap, try to make answer more concise
                logger.info("Detected potential repetition, making answer more concise")
                # Could implement more sophisticated deduplication here
    
    # Add context-aware transitions
    if intent == "continue" and conversation_history:
        # Check if this is a follow-up to a previous question
        if any(word in answer.lower() for word in ["además", "también", "así mismo"]):
            # Already has transition, keep as is
            pass
        else:
            # Could add subtle transition if needed
            pass
    
    return answer
