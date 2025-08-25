# NEW CODE
"""
Agent graph:
- agent: LLM with tools
- action: ToolNode
- helpfulness: Y/N verifier
"""

from __future__ import annotations
from typing import Dict, Any
import json

from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langchain_core.messages import AIMessage, ToolMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import HumanMessage, SystemMessage

from ..core.state import AgentState
from ..models import get_chat_model
from ..tools.toolbelt import get_tool_belt
from ..core.prompts import HELPFULNESS_PROMPT, ADN_SYSTEM_PROMPT
from ..timezone_utils import get_contextual_time_info
from app.core.logger import logger


def _build_model_with_tools():
    """Returns chat model bound to tools."""
    try:
        logger.info("🤖 [GRAPH] Building model with tools...")
        model = get_chat_model()
        tools = get_tool_belt()
        bound_model = model.bind_tools(tools)
        logger.info(f"✅ [GRAPH] Model bound with {len(tools)} tools successfully")
        return bound_model
    except Exception as e:
        logger.error(f"❌ [GRAPH] Failed to build model with tools: {str(e)}")
        raise


def call_model(state: AgentState) -> Dict[str, Any]:
    """
    Invokes the LLM with system + state snapshot to force the flow.
    """
    try:
        conversation_id = state.get("conversation_id", "unknown")
        current_attempt = state.get("attempts", 0)
        target_lang = state.get("target_language", "en")

        if current_attempt >= 3:
            fallback_message = ("I'm sorry, I don't have the specific information you need at this moment. "
                                "Please wait, a human agent will respond to you shortly.")
            return {"messages": [AIMessage(content=fallback_message)], "attempts": current_attempt + 1}

        model = _build_model_with_tools()

        # Temporal context (English date only) + stage/contract snapshot
        time_context = get_contextual_time_info("en")
        system_prompt = ADN_SYSTEM_PROMPT.format(time_context=time_context)

        # Build minimal snapshot that the model can read without excessive tokens
        stage = state.get("stage", "idle")
        contract = state.get("contract", {})
        snapshot = {
            "stage": stage,
            "selection": contract.get("selection"),
            "customer": {k: contract.get("customer", {}).get(k) for k in ("full_name", "email", "mobile_number", "identification_number")},
            "booking": contract.get("booking"),
            "confirmations": contract.get("confirmations"),
        }

        snapshot_msg = SystemMessage(content=f"[FLOW_SNAPSHOT]\n{snapshot}")

        # Messages: system + snapshot + user/agent history
        messages = [SystemMessage(content=system_prompt), snapshot_msg]
        messages.extend(state["messages"][1:] if state.get("messages") else [])

        response = model.invoke(messages)

        # Log tool calls vs direct response
        tool_calls = getattr(response, "tool_calls", None)
        if tool_calls:
            logger.info(f"🔧 [GRAPH] Model calls: {[tc.get('name') for tc in tool_calls]}")
        else:
            logger.info(f"💬 [GRAPH] Direct response: {response.content[:100]}...")

        return {"messages": [response], "attempts": current_attempt + 1}

    except Exception as e:
        logger.error(f"❌ [GRAPH] Agent node failed: {str(e)}")
        return {"messages": [AIMessage(content=f"Agent error: {str(e)}")], "attempts": state.get("attempts", 0) + 1}


def route_to_action_or_helpfulness(state: AgentState):
    """Route: execute tools or evaluate helpfulness."""
    try:
        last_message = state["messages"][-1]
        tool_calls = getattr(last_message, "tool_calls", None)
        
        if tool_calls:
            logger.info(f"🔧 [GRAPH] Routing to ACTION - {len(tool_calls)} tool calls to execute")
            return "action"
        else:
            logger.info("🤔 [GRAPH] Routing to HELPFULNESS - evaluating response quality")
            return "helpfulness"
            
    except Exception as e:
        logger.error(f"❌ [GRAPH] Routing failed: {str(e)}")
        return "helpfulness"  # Default fallback


def helpfulness_node(state: AgentState) -> Dict[str, Any]:
    """Evaluates Y/N with attempt limit to avoid loops."""
    try:
        attempts = state.get("attempts", 0)
        conversation_id = state.get("conversation_id", "unknown")
        
        logger.info(f"🤔 [GRAPH] Helpfulness node - conversation: {conversation_id}, attempt: {attempts}")
        
        if attempts >= 3:
            logger.info("🔄 [GRAPH] Maximum attempts reached (3), ending helpfulness loop")
            return {"messages": [AIMessage(content="HELPFULNESS:END")]}
            
        # Find the LAST human query in this conversation (not the first!)
        initial_query = ""
        for m in reversed(state["messages"]):  # Search backwards to get the LATEST query
            if getattr(m, "type", None) == "human" or getattr(m, "role", "") == "user":
                initial_query = getattr(m, "content", "")
                break

        final_response = state["messages"][-1].content
        
        logger.info(f"🤔 [GRAPH] Evaluating helpfulness - query: '{initial_query[:50]}...', response: '{final_response[:50]}...'")
        
        # Check for simple greetings - these should be considered helpful
        # But exclude queries that also ask for information (like "hola, que servicios tienen?")
        query_lower = initial_query.lower().strip()
        greeting_patterns = ["hola", "hello", "hi", "hey", "buenas", "buenos días", "buenas tardes", "buenas noches", "good morning", "good afternoon", "good evening"]
        
        # Don't consider it a simple greeting if it contains question words or service-related terms
        question_indicators = ["que", "what", "como", "how", "cuando", "when", "donde", "where", "servicios", "services", "planes", "plans", "precios", "prices", "?"]
        has_questions = any(indicator in query_lower for indicator in question_indicators)
        
        if any(pattern in query_lower for pattern in greeting_patterns) and len(query_lower) < 20 and not has_questions:
            logger.info("🤔 [GRAPH] Detected simple greeting, considering response helpful")
            return {"messages": [AIMessage(content="HELPFULNESS:Y")]}
        
        # Check if the response indicates empty knowledge base
        if "configurando mi base de conocimiento" in final_response or "setting up my knowledge base" in final_response:
            logger.info("🤔 [GRAPH] Detected knowledge base setup message, considering helpful")
            return {"messages": [AIMessage(content="HELPFULNESS:Y")]}
        
        chain = HELPFULNESS_PROMPT | get_chat_model() | StrOutputParser()
        decision = chain.invoke({"initial_query": initial_query, "final_response": final_response})
        decision = "Y" if "Y" in decision else "N"
        
        logger.info(f"🤔 [GRAPH] Helpfulness decision: {decision}")
        
        return {"messages": [AIMessage(content=f"HELPFULNESS:{decision}")]}
        
    except Exception as e:
        logger.error(f"❌ [GRAPH] Helpfulness node failed: {str(e)}")
        # Default to "Y" to end the loop on error
        return {"messages": [AIMessage(content="HELPFULNESS:Y")]}


def helpfulness_decision(state: AgentState):
    """Closes on Y/END or continues."""
    try:
        text = getattr(state["messages"][-1], "content", "")
        conversation_id = state.get("conversation_id", "unknown")
        
        if "HELPFULNESS:END" in text:
            logger.info(f"🔄 [GRAPH] Helpfulness decision: END - conversation: {conversation_id}")
            return END
        elif "HELPFULNESS:Y" in text:
            logger.info(f"✅ [GRAPH] Helpfulness decision: SATISFIED - conversation: {conversation_id}")
            return "end"
        else:
            logger.info(f"🔄 [GRAPH] Helpfulness decision: CONTINUE - conversation: {conversation_id}")
            return "continue"
            
    except Exception as e:
        logger.error(f"❌ [GRAPH] Helpfulness decision failed: {str(e)}")
        return "end"  # Default to ending on error


async def action_node(state: AgentState) -> Dict[str, Any]:
    """
    Executes tool calls. For critical tools like `get_available_slots`, emit a final AI message
    with a deterministic, user-ready string (do not rely on the LLM to render).
    """
    try:
        last_message = state["messages"][-1]
        tool_calls = getattr(last_message, "tool_calls", [])
        
        if not tool_calls:
            logger.warning("🔧 [GRAPH] Action node called but no tool calls found")
            return state
        
        tools = get_tool_belt()
        tool_messages = []
        emitted_final = False
        last_action = None
        
        for tool_call in tool_calls:
            tool_name = tool_call.get("name")
            tool_args = tool_call.get("args", {})
            last_action = tool_name
            
            logger.info(f"🔧 [GRAPH] Executing tool: {tool_name} with args: {tool_args}")
            
            # Find the tool
            tool = None
            for t in tools:
                if hasattr(t, 'name') and t.name == tool_name:
                    tool = t
                    break
            
            if not tool:
                logger.warning(f"🔧 [GRAPH] Tool {tool_name} not found")
                tool_messages.append(ToolMessage(
                    content=f"ERROR: Tool {tool_name} not found",
                    tool_call_id=tool_call.get("id")
                ))
                continue
            
            try:
                # Execute the tool ASYNC
                result = await tool.ainvoke(tool_args)
                
                # Check if tool execution returned an error
                if isinstance(result, str) and result.startswith(("ERROR_ACCESSING_KNOWLEDGE:", "NO_CONTEXT_AVAILABLE:")):
                    logger.warning(f"🔧 [GRAPH] Tool {tool_name} returned error: {result}")
                else:
                    logger.info(f"🔧 [GRAPH] Tool {tool_name} executed successfully, result length: {len(str(result))}")
                
                # Add tool result message
                tool_messages.append(ToolMessage(
                    content=str(result),
                    tool_call_id=tool_call.get("id")
                ))
                
                # Deterministic post-processing: slots must be shown in the SAME turn
                if tool_name == "get_available_slots":
                    try:
                        data = json.loads(result) if isinstance(result, str) else result
                        whatsapp_text = data.get("whatsapp_text")
                        if whatsapp_text:
                            # Emit final AI message with the preformatted list
                            logger.info(f"🔧 [GRAPH] Emitting final WhatsApp message for slots: {whatsapp_text[:100]}...")
                            tool_messages.append(AIMessage(content=whatsapp_text))
                            emitted_final = True
                        else:
                            logger.warning("🔧 [GRAPH] No whatsapp_text found in get_available_slots result")
                    except Exception as parse_error:
                        logger.warning(f"⚠️ [GRAPH] Failed to parse slots result: {parse_error}")
                        
            except Exception as tool_error:
                logger.error(f"❌ [GRAPH] Tool {tool_name} failed: {str(tool_error)}")
                tool_messages.append(ToolMessage(
                    content=f"ERROR_ACCESSING_KNOWLEDGE: Tool execution failed - {str(tool_error)}",
                    tool_call_id=tool_call.get("id")
                ))
        
        # If we emitted a final user message, advance stage and short-circuit next hop to helpfulness
        update: Dict[str, Any] = {"messages": state["messages"] + tool_messages}
        if emitted_final:
            update["stage"] = "schedule"
            update["last_action"] = f"{last_action}_emit"
            logger.info("🔧 [GRAPH] Emitted final message, setting stage to 'schedule' and marking for helpfulness routing")
        elif last_action:
            update["last_action"] = last_action
        
        return update
        
    except Exception as e:
        logger.error(f"❌ [GRAPH] Action node failed: {str(e)}")
        # Add error message as a regular AI message
        error_message = AIMessage(content=f"ERROR_ACCESSING_KNOWLEDGE: {str(e)}")
        return {"messages": state["messages"] + [error_message]}


def route_after_action(state: AgentState):
    """
    If we already emitted a final user-facing payload (e.g., slots list),
    skip helpfulness and go straight to END; otherwise return to agent.
    """
    last_action = state.get("last_action", "")
    has_final_message = False
    
    # Check if the last message is an AI message (indicating we emitted a final response)
    if state.get("messages") and isinstance(state["messages"][-1], AIMessage):
        # Check if this is from get_available_slots tool that emitted final message
        if last_action.startswith("get_available_slots") and last_action.endswith("_emit"):
            has_final_message = True
    
    if has_final_message:
        logger.info(f"🔄 [GRAPH] Emitted final message - going directly to END to skip helpfulness check (last_action: {last_action})")
        return "end"
    else:
        logger.info(f"🔄 [GRAPH] Routing back to agent (last_action: {last_action})")
        return "agent"


def build_graph():
    """Compiles graph."""
    try:
        logger.info("🏗️ [GRAPH] Building agent graph...")
        
        graph = StateGraph(AgentState)

        # Add nodes (using custom action node instead of ToolNode)
        graph.add_node("agent", call_model)
        graph.add_node("action", action_node)
        graph.add_node("helpfulness", helpfulness_node)

        # Set entry point
        graph.set_entry_point("agent")
        
        # Add conditional edges
        graph.add_conditional_edges("agent", route_to_action_or_helpfulness,
                                    {"action": "action", "helpfulness": "helpfulness"})
        graph.add_conditional_edges("helpfulness", helpfulness_decision,
                                    {"continue": "agent", "end": END, END: END})
        
        # NEW: post-action conditional routing (short-circuit when we already emitted the final message)
        graph.add_conditional_edges("action", route_after_action, 
                                    {"agent": "agent", "end": END})
        
        compiled_graph = graph.compile()
        logger.info("✅ [GRAPH] Agent graph compiled successfully")
        
        return compiled_graph
        
    except Exception as e:
        logger.error(f"❌ [GRAPH] Failed to build agent graph: {str(e)}")
        raise
