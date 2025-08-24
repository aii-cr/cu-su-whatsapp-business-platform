# NEW CODE
"""
Ejecución del agente por conversación:
- LangSmith tracing
- Carga memoria Mongo
- Detección de idioma simple
- Invocación del grafo
"""

from __future__ import annotations
from typing import List
import re
import time

from langchain_core.messages import HumanMessage, SystemMessage, AIMessage

from app.services.ai.shared.memory_service import memory_service
from .agent_graph import build_graph
from .prompts import ADN_SYSTEM_PROMPT
from .telemetry import setup_tracing
from app.core.logger import logger


def _infer_language(text: str) -> str:
    """Heurística ligera para detectar 'en' vs 'es'."""
    try:
        t = text.lower()
        en_hits = sum(1 for w in ("the","and","what","how","price","channel","plan","install","coverage") if w in t)
        es_hits = sum(1 for w in ("el","la","los","las","qué","como","precio","canal","plan","instalación","cobertura") if w in t)
        detected_lang = "en" if en_hits > es_hits else "es"
        
        logger.info(f"🌐 [RUNNER] Language detection - text: '{text[:50]}...', en_hits: {en_hits}, es_hits: {es_hits}, detected: {detected_lang}")
        return detected_lang
        
    except Exception as e:
        logger.error(f"❌ [RUNNER] Language detection failed: {str(e)}")
        return "es"  # Default to Spanish


def _prepare_history_messages(history: List[dict], target_language: str) -> List:
    """Convierte historial en mensajes (inyecta system bilingüe)."""
    try:
        logger.info(f"📚 [RUNNER] Preparing {len(history)} history messages with target language: {target_language}")
        
        msgs: List = [SystemMessage(content=ADN_SYSTEM_PROMPT.format(target_language=target_language))]
        
        for i, h in enumerate(history):
            role = h.get("role")
            content = h.get("content", "")
            if not content:
                continue
                
            if role == "user":
                msgs.append(HumanMessage(content=content))
                logger.debug(f"📚 [RUNNER] Added user message {i+1}: '{content[:50]}...'")
            elif role == "assistant":
                msgs.append(AIMessage(content=content))
                logger.debug(f"📚 [RUNNER] Added assistant message {i+1}: '{content[:50]}...'")
                
        logger.info(f"✅ [RUNNER] Prepared {len(msgs)} total messages (including system message)")
        return msgs
        
    except Exception as e:
        logger.error(f"❌ [RUNNER] Failed to prepare history messages: {str(e)}")
        # Return minimal system message
        return [SystemMessage(content=ADN_SYSTEM_PROMPT.format(target_language=target_language))]


async def run_agent(conversation_id: str, user_text: str) -> str:
    """Ejecuta el agente para una conversación y retorna la respuesta."""
    start_time = time.time()
    
    try:
        logger.info(f"🚀 [RUNNER] Starting agent execution - conversation: {conversation_id}")
        logger.info(f"📝 [RUNNER] User input: '{user_text[:100]}...'")
        
        # Step 1: LangSmith tracing setup
        logger.info("🔍 [RUNNER] Setting up LangSmith tracing...")
        setup_tracing()

        # Step 2: Memory and history compression
        logger.info("📚 [RUNNER] Loading conversation context...")
        ctx = await memory_service.get_conversation_context(conversation_id)
        history = ctx.get("history", [])
        
        original_history_len = len(history)
        if len(history) > 10 and ctx.get("summary"):
            history = [{"role": "assistant", "content": f"Resumen: {ctx['summary']}"}] + history[-6:]
            logger.info(f"📚 [RUNNER] Compressed history from {original_history_len} to {len(history)} messages")
        else:
            logger.info(f"📚 [RUNNER] Using full history: {len(history)} messages")

        # Step 3: Language detection
        logger.info("🌐 [RUNNER] Detecting target language...")
        target_language = _infer_language(user_text)

        # Step 4: Graph setup and input preparation
        logger.info("🏗️ [RUNNER] Building agent graph...")
        graph = build_graph()
        
        logger.info("📝 [RUNNER] Preparing input messages...")
        messages = _prepare_history_messages(history, target_language)
        messages.append(HumanMessage(content=user_text))

        # Step 5: Execute agent graph
        logger.info(f"🎯 [RUNNER] Executing agent graph with {len(messages)} messages...")
        
        graph_start_time = time.time()
        result = graph.invoke({
            "messages": messages,
            "conversation_id": conversation_id,
            "attempts": 0,
            "target_language": target_language
        })
        graph_execution_time = time.time() - graph_start_time
        
        logger.info(f"✅ [RUNNER] Graph execution completed in {graph_execution_time:.2f}s")
        
        # Debug: Log the complete result structure
        logger.info(f"🔍 [RUNNER] Graph result keys: {list(result.keys())}")
        logger.info(f"🔍 [RUNNER] Total messages in result: {len(result.get('messages', []))}")
        
        # Step 6: Extract final answer
        ai_msgs = [m for m in result["messages"] if isinstance(m, AIMessage)]
        logger.info(f"🔍 [RUNNER] Found {len(ai_msgs)} AI messages in result")
        
        if ai_msgs:
            # Debug: Log all AI messages to understand the structure
            for i, msg in enumerate(ai_msgs):
                content = getattr(msg, "content", "")
                logger.info(f"🔍 [RUNNER] AI Message {i+1}: '{content[:100]}...'")
            
            # Find the last substantive response (non-helpfulness message)
            final_response = None
            substantive_responses = []
            
            for msg in ai_msgs:
                content = getattr(msg, "content", "")
                if content and not content.startswith("HELPFULNESS:"):
                    substantive_responses.append(content)
                    logger.info(f"🔍 [RUNNER] Found substantive response: '{content[:50]}...'")
            
            if substantive_responses:
                final_response = substantive_responses[-1]  # Get the last substantive response
                logger.info(f"💬 [RUNNER] Found {len(substantive_responses)} substantive responses, using: '{final_response[:100]}...'")
            
            if final_response:
                answer = final_response
            else:
                # Detect language for appropriate fallback message
                target_lang = _infer_language(user_text)
                if target_lang == "en":
                    answer = "I'm sorry, I couldn't generate a complete response. Please wait, a human agent will respond to you shortly."
                else:
                    answer = "Lo siento, no se pudo completar la respuesta. Por favor espera que enseguida te responde un agente humano."
                logger.warning("⚠️ [RUNNER] No substantive response found in AI messages")
        else:
            # Detect language for appropriate fallback message  
            target_lang = _infer_language(user_text)
            if target_lang == "en":
                answer = "I'm sorry, I couldn't process your request. Please wait, a human agent will respond to you shortly."
            else:
                answer = "Lo siento, no se pudo procesar tu solicitud. Por favor espera que enseguida te responde un agente humano."
            logger.warning("⚠️ [RUNNER] No AI messages found in result")

        logger.info(f"💬 [RUNNER] Final answer: '{answer[:100]}...'")

        # Step 7: Persist memory
        logger.info("💾 [RUNNER] Persisting interaction to memory...")
        await memory_service.add_interaction_to_memory(conversation_id, user_text, answer)
        
        total_execution_time = time.time() - start_time
        logger.info(f"🎉 [RUNNER] Agent execution completed successfully in {total_execution_time:.2f}s")
        
        return answer
        
    except Exception as e:
        execution_time = time.time() - start_time
        logger.error(f"❌ [RUNNER] Agent execution failed after {execution_time:.2f}s: {str(e)}")
        
        # Detect language for appropriate error message
        target_lang = _infer_language(user_text)
        
        if target_lang == "en":
            return "I'm sorry, I couldn't process your request right now. Please wait, a human agent will respond to you shortly."
        else:
            return "Lo siento, no se pudo procesar su solicitud ahora mismo. Por favor espera que enseguida te responde un agente humano."
