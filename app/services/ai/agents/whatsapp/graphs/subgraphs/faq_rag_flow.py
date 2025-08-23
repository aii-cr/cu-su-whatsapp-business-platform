"""
FAQ/RAG flow subgraph using the new hybrid retriever.
Retrieves relevant documents and synthesizes answers using the RAG prompt.
"""

from typing import Dict, Any
from app.core.logger import logger
from app.services.ai.agents.whatsapp.tools.rag_tool import RAGTool
from app.services.ai.config import ai_config
from app.services.ai.rag.retriever import build_retriever
from app.services.ai.rag.schemas import RetrievalMethod


async def run_rag_flow(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute the RAG flow for FAQ-type queries using the new hybrid retriever.
    
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
        
        # Use WhatsApp RAG tool to get raw document content
        from app.services.ai.agents.whatsapp.tools.rag_tool import RAGTool
        
        # Enhance query with conversation context
        enhanced_query = _enhance_query_with_context(
            state["user_text"], 
            state.get("conversation_history", []),
            state.get("conversation_summary", "")
        )
        
        logger.info(f"Enhanced query: '{enhanced_query[:100]}...'")
        
        # Get raw document content from WhatsApp RAG tool
        rag_tool = RAGTool()
        rag_result = await rag_tool.execute_with_timeout(
            query=enhanced_query,
            tenant_id=None,  # Disable filtering for now
            locale=None,     # Disable filtering for now
            max_context_length=ai_config.max_context_tokens
        )
        
        if rag_result["status"] == "success":
            # Synthesize answer using LLM with proper prompt (like writer agent)
            answer = await _synthesize_answer_with_llm(
                question=state["user_text"],
                context=rag_result["data"]["answer"],  # Raw document content
                conversation_history=state.get("conversation_history", [])
            )
        else:
            answer = f"Error: {rag_result.get('error', 'Unknown error')}"
        
        if answer and not answer.startswith("Error"):
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
            
            # Post-process answer based on conversation context
            processed_answer = _post_process_answer(
                answer, 
                state.get("conversation_history", []),
                state.get("intent", "faq")
            )
            
            # Update state
            state["reply"] = processed_answer
            state["confidence"] = 0.8  # High confidence for successful LLM synthesis
            state["tool_result"] = {
                "answer": answer,
                "context": rag_result["data"]["answer"],  # Raw document content
                "method": "shared_rag_with_llm_synthesis"
            }
            state["context_docs"] = []  # Context is in the tool_result
            
            # Check if we need human handoff based on confidence
            if state["confidence"] < ai_config.confidence_threshold:
                state["requires_human_handoff"] = True
                
                # Append handoff message if confidence is very low
                if state["confidence"] < 0.3:
                    state["reply"] += "\n\n¿Te gustaría que te conecte con un agente?"
            
            logger.info(
                f"RAG flow completed successfully (confidence: {state['confidence']:.2f})"
            )
            
        else:
            # Handle LLM synthesis failure
            logger.error(f"LLM synthesis failed: {answer}")
            
            state["reply"] = "Lo siento, no puedo acceder a la información en este momento. Te conectaré con un agente."
            state["confidence"] = 0.0
            state["requires_human_handoff"] = True
            state["tool_result"] = {
                "error": answer,
                "status": "llm_synthesis_failed"
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


async def run_hybrid_rag_flow(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute the RAG flow using the new hybrid retriever directly.
    This is an alternative implementation that bypasses the RAG tool.
    
    Args:
        state: Agent state dictionary
        
    Returns:
        Updated state with RAG results
    """
    state["node_history"] = state.get("node_history", []) + ["hybrid_rag"]
    
    logger.info(f"Running hybrid RAG flow for query: '{state['user_text'][:50]}...'")
    
    try:
        # Build hybrid retriever
        retriever = build_retriever(
            tenant_id=None,  # Disable filtering for now
            locale=state.get("customer_language", "es_CR"),
            k=10,
            score_threshold=0.20,
            method=RetrievalMethod.DENSE,
            enable_multi_query=True,
            enable_compression=True
        )
        
        # Enhance query
        enhanced_query = _enhance_query_with_context(
            state["user_text"], 
            state.get("conversation_history", []),
            state.get("conversation_summary", "")
        )
        
        # Retrieve documents
        retrieval_result = await retriever.get_retrieval_result(enhanced_query)
        
        if retrieval_result.documents:
            # Format context for RAG prompt
            context = _format_context_for_rag(retrieval_result.documents)
            
            # Generate answer using RAG prompt
            answer = await _generate_rag_answer(enhanced_query, context)
            
            # Calculate confidence based on retrieval scores
            confidence = _calculate_confidence(retrieval_result.scores)
            
            # Update state
            state["reply"] = answer
            state["confidence"] = confidence
            state["tool_result"] = {
                "retrieval_metadata": {
                    "method": retrieval_result.method,
                    "expanded_queries": retrieval_result.expanded_queries,
                    "filters_applied": retrieval_result.filters_applied,
                    "threshold_used": retrieval_result.threshold_used,
                    "metadata_overrides": retrieval_result.metadata_overrides
                }
            }
            state["context_docs"] = [
                {
                    "content": doc.content,
                    "source": doc.source,
                    "section": doc.section,
                    "score": score
                }
                for doc, score in zip(retrieval_result.documents, retrieval_result.scores)
            ]
            
            logger.info(
                f"Hybrid RAG completed: {len(retrieval_result.documents)} docs, "
                f"confidence: {confidence:.2f}"
            )
            
        else:
            # No documents found
            state["reply"] = "Lo siento, no encuentro esa información en este momento 🙏. ¿Te ayudo con otra cosa?"
            state["confidence"] = 0.0
            state["tool_result"] = {"error": "No documents found"}
        
    except Exception as e:
        logger.error(f"Error in hybrid RAG flow: {str(e)}")
        state["reply"] = "Lo siento, ocurrió un error procesando tu consulta."
        state["confidence"] = 0.0
        state["tool_result"] = {"error": str(e)}
    
    return state


def _format_context_for_rag(documents) -> str:
    """Format retrieved documents for RAG prompt."""
    context_parts = []
    
    for doc in documents:
        # Format each document with metadata
        meta_info = f"[{doc.source} | {doc.section}"
        if doc.subsection:
            meta_info += f" > {doc.subsection}"
        meta_info += f" | {doc.updated_at.strftime('%Y-%m-%d')}]"
        
        context_parts.append(f"{meta_info}\n{doc.content}")
    
    return "\n\n".join(context_parts)


async def _generate_rag_answer(query: str, context: str) -> str:
    """Generate answer using RAG prompt."""
    try:
        from pathlib import Path
        from langchain_core.prompts import ChatPromptTemplate
        from langchain_openai import ChatOpenAI
        
        # Load RAG prompt
        prompt_path = Path("app/services/ai/agents/whatsapp/prompts/system/rag_answer.md")
        prompt_content = prompt_path.read_text(encoding="utf-8")
        
        # Create chain
        prompt = ChatPromptTemplate.from_template(prompt_content)
        llm = ChatOpenAI(
            openai_api_key=ai_config.openai_api_key,
            model=ai_config.openai_model,
            temperature=0.1
        )
        chain = prompt | llm
        
        # Generate answer
        result = await chain.ainvoke({
            "question": query,
            "context": context
        })
        
        return result.content.strip()
        
    except Exception as e:
        logger.error(f"Error generating RAG answer: {str(e)}")
        return "Lo siento, no puedo generar una respuesta en este momento."


async def _synthesize_answer_with_llm(question: str, context: str, conversation_history: list) -> str:
    """Synthesize answer using LLM with proper prompt (like writer agent)."""
    try:
        from pathlib import Path
        from langchain_core.prompts import ChatPromptTemplate
        from langchain_openai import ChatOpenAI
        from app.services.ai.config import ai_config
        
        # Load RAG answer prompt
        prompt_path = Path(__file__).parent.parent.parent / "prompts" / "system" / "rag_answer.md"
        prompt_content = prompt_path.read_text(encoding="utf-8")
        
        # Create chain
        prompt = ChatPromptTemplate.from_template(prompt_content)
        llm = ChatOpenAI(
            openai_api_key=ai_config.openai_api_key,
            model=ai_config.openai_model,
            temperature=0.1
        )
        chain = prompt | llm
        
        # Generate answer
        result = await chain.ainvoke({
            "question": question,
            "context": context
        })
        
        return result.content.strip()
        
    except Exception as e:
        logger.error(f"Error synthesizing answer with LLM: {str(e)}")
        return f"Error: {str(e)}"


def _calculate_confidence(scores: list) -> float:
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
