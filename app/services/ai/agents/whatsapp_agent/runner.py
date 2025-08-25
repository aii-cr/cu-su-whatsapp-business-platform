# NEW CODE
"""
Agent execution by conversation:
- LangSmith tracing
- Mongo memory loading
- Graph invocation (English-only)
"""

from __future__ import annotations
from typing import List
import time

from langchain_core.messages import HumanMessage, SystemMessage, AIMessage

from app.services.ai.shared.memory_service import memory_service
from .graph.agent_graph import build_graph
from .core.prompts import ADN_SYSTEM_PROMPT
from .telemetry import setup_tracing
from app.core.logger import logger


def _english_only_fallback() -> str:
    """Consistent English fallback message."""
    return "I'm sorry, I couldn't process your request right now. Please wait, a human agent will respond to you shortly."


def _prepare_history_messages(history: List[dict]) -> List:
    """Converts history to messages (injects English-only system)."""
    try:
        logger.info(f"📚 [RUNNER] Preparing {len(history)} history messages (English-only)")
        
        # Get today's date (English) for context
        from .timezone_utils import get_contextual_time_info
        time_context = get_contextual_time_info("en")
        
        msgs: List = [SystemMessage(content=ADN_SYSTEM_PROMPT.format(time_context=time_context))]
        
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
        # Return minimal system message with empty date
        return [SystemMessage(content=ADN_SYSTEM_PROMPT.format(time_context=""))]


async def run_agent(conversation_id: str, user_text: str) -> str:
    """Executes the agent for a conversation and returns the response."""
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
            history = [{"role": "assistant", "content": f"Summary: {ctx['summary']}"}] + history[-6:]
            logger.info(f"📚 [RUNNER] Compressed history from {original_history_len} to {len(history)} messages")
        else:
            logger.info(f"📚 [RUNNER] Using full history: {len(history)} messages")

        # Step 3: English-only configuration
        logger.info("🌐 [RUNNER] Using English-only configuration...")

        # Step 4: Graph setup and input preparation
        logger.info("🏗️ [RUNNER] Building agent graph...")
        graph = build_graph()
        
        logger.info("📝 [RUNNER] Preparing input messages...")
        messages = _prepare_history_messages(history)
        messages.append(HumanMessage(content=user_text))

        # Step 5: Execute agent graph
        logger.info(f"🎯 [RUNNER] Executing agent graph with {len(messages)} messages...")
        
        graph_start_time = time.time()
        result = await graph.ainvoke({
            "messages": messages,
            "conversation_id": conversation_id,
            "attempts": 0,
            "target_language": "en",
            "stage": "idle",
            "contract": {
                "selection": {},
                "customer": {},
                "booking": {},
                "confirmations": {"selection_confirmed": False, "booking_confirmed": False, "email_sent": False}
            },
            "system_snapshot": None,
            "last_action": None
        })
        graph_execution_time = time.time() - graph_start_time
        
        logger.info(f"✅ [RUNNER] Graph execution completed in {graph_execution_time:.2f}s")
        
        # Step 6: Extract final answer
        ai_msgs = [m for m in result["messages"] if isinstance(m, AIMessage)]
        if ai_msgs:
            # Find the last non-helpfulness message
            final_response = None
            for msg in reversed(ai_msgs):
                content = getattr(msg, "content", "")
                if not content.startswith("HELPFULNESS:"):
                    final_response = content
                    break
            
            if final_response:
                answer = final_response
            else:
                answer = _english_only_fallback()
        else:
            # English-only fallback
            answer = _english_only_fallback()
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
        
        return _english_only_fallback()
