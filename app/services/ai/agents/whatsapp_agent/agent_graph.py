# NEW CODE
"""
Grafo del agente:
- agent: LLM con tools
- action: ToolNode
- helpfulness: verificador Y/N
"""

from __future__ import annotations
from typing import Dict, Any

from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langchain_core.messages import AIMessage, ToolMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import HumanMessage, SystemMessage

from .state import AgentState
from .models import get_chat_model
from .tools import get_tool_belt
from .prompts import HELPFULNESS_PROMPT, ADN_SYSTEM_PROMPT
from .timezone_utils import get_contextual_time_info
from app.core.logger import logger


def _build_model_with_tools():
    """Devuelve chat model bind a herramientas."""
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
    """Invoca el LLM con sistema bilingüe + mensajes acumulados."""
    try:
        conversation_id = state.get("conversation_id", "unknown")
        current_attempt = state.get("attempts", 0)
        target_lang = state.get("target_language", "es")
        
        logger.info(f"🤖 [GRAPH] Agent node - conversation: {conversation_id}, attempt: {current_attempt + 1}, lang: {target_lang}")
        
        # Check for maximum attempts before using tools (reduced from 6 to 3)
        if current_attempt >= 3:
            logger.warning(f"🛑 [GRAPH] Maximum attempts reached ({current_attempt}), forcing final response")
            fallback_message = "Lo siento, no tengo la información específica que necesitas en este momento. Por favor espera que enseguida te responde un agente humano."
            return {"messages": [AIMessage(content=fallback_message)], "attempts": current_attempt + 1}
        
        # DISABLE ERROR DETECTION - Let the agent work like Writer agent
        # The Writer agent doesn't have this logic and works perfectly
        # This was causing false positives and premature fallbacks
        
        model = _build_model_with_tools()

        # Get current time context for Costa Rica
        time_context = get_contextual_time_info("es")  # Time context in Spanish for Costa Rica
        
        # Reescribe el primer mensaje como SystemMessage con contexto temporal.
        system_prompt = ADN_SYSTEM_PROMPT.format(time_context=time_context)
        messages = [SystemMessage(content=system_prompt)]
        messages.extend(state["messages"][1:] if state["messages"] else [])
        
        logger.info(f"🤖 [GRAPH] Invoking model with {len(messages)} messages...")
        response = model.invoke(messages)
        
        # Log if the model wants to use tools
        tool_calls = getattr(response, "tool_calls", None)
        if tool_calls:
            logger.info(f"🔧 [GRAPH] Model wants to use {len(tool_calls)} tools: {[tc.get('name', 'unknown') for tc in tool_calls]}")
        else:
            logger.info(f"💬 [GRAPH] Model generated direct response: {response.content[:100]}...")
        
        result = {"messages": [response], "attempts": current_attempt + 1}
        logger.info(f"✅ [GRAPH] Agent node completed successfully")
        return result
        
    except Exception as e:
        logger.error(f"❌ [GRAPH] Agent node failed: {str(e)}")
        # Return a failure response instead of raising
        return {"messages": [AIMessage(content=f"Error en el agente: {str(e)}")], "attempts": state.get("attempts", 0) + 1}


def route_to_action_or_helpfulness(state: AgentState):
    """Ruta: ejecutar herramientas o evaluar utilidad."""
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
    """Evalúa Y/N con tope de intentos para evitar loops."""
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
    """Cierra en Y/END o continúa."""
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
    """Execute tool calls with proper error handling."""
    try:
        last_message = state["messages"][-1]
        tool_calls = getattr(last_message, "tool_calls", [])
        
        if not tool_calls:
            logger.warning("🔧 [GRAPH] Action node called but no tool calls found")
            return state
        
        tools = get_tool_belt()
        tool_results = []
        
        for tool_call in tool_calls:
            tool_name = tool_call.get("name")
            tool_args = tool_call.get("args", {})
            
            logger.info(f"🔧 [GRAPH] Executing tool: {tool_name} with args: {tool_args}")
            
            # Find the tool
            tool = None
            for t in tools:
                if hasattr(t, 'name') and t.name == tool_name:
                    tool = t
                    break
            
            if tool:
                try:
                    # Execute the tool ASYNC (like Writer agent does)
                    result = await tool.ainvoke(tool_args)
                    
                    # Check if tool execution returned an error (like Writer agent does)
                    if isinstance(result, str) and result.startswith(("ERROR_ACCESSING_KNOWLEDGE:", "NO_CONTEXT_AVAILABLE:")):
                        logger.warning(f"🔧 [GRAPH] Tool {tool_name} returned error: {result}")
                    else:
                        logger.info(f"🔧 [GRAPH] Tool {tool_name} executed successfully, result length: {len(str(result))}")
                        
                    tool_results.append({
                        "role": "tool",
                        "content": str(result),
                        "tool_call_id": tool_call.get("id"),
                        "name": tool_name
                    })
                    
                except Exception as tool_error:
                    logger.error(f"❌ [GRAPH] Tool {tool_name} failed: {str(tool_error)}")
                    tool_results.append({
                        "role": "tool", 
                        "content": f"ERROR_ACCESSING_KNOWLEDGE: Tool execution failed - {str(tool_error)}",
                        "tool_call_id": tool_call.get("id"),
                        "name": tool_name
                    })
            else:
                logger.warning(f"🔧 [GRAPH] Tool {tool_name} not found")
                tool_results.append({
                    "role": "tool",
                    "content": f"ERROR: Tool {tool_name} not found",
                    "tool_call_id": tool_call.get("id"),
                    "name": tool_name
                })
        
        # Convert tool results to ToolMessage objects for LangGraph compatibility
        tool_messages = []
        for result in tool_results:
            tool_messages.append(ToolMessage(
                content=result["content"],
                tool_call_id=result.get("tool_call_id")
            ))
        
        # Add tool results to state
        return {"messages": state["messages"] + tool_messages}
        
    except Exception as e:
        logger.error(f"❌ [GRAPH] Action node failed: {str(e)}")
        # Add error message as a regular AI message
        error_message = AIMessage(content=f"ERROR_ACCESSING_KNOWLEDGE: {str(e)}")
        return {"messages": state["messages"] + [error_message]}


def build_graph():
    """Compila grafo."""
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
        
        # Add direct edge from action back to agent
        graph.add_edge("action", "agent")
        
        compiled_graph = graph.compile()
        logger.info("✅ [GRAPH] Agent graph compiled successfully")
        
        return compiled_graph
        
    except Exception as e:
        logger.error(f"❌ [GRAPH] Failed to build agent graph: {str(e)}")
        raise
