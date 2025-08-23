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
from langchain_core.messages import AIMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import HumanMessage, SystemMessage

from .state import AgentState
from .models import get_chat_model
from .tools import get_tool_belt
from .prompts import HELPFULNESS_PROMPT, ADN_SYSTEM_PROMPT
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
        
        model = _build_model_with_tools()

        # Reescribe el primer mensaje como SystemMessage con idioma objetivo.
        messages = [SystemMessage(content=ADN_SYSTEM_PROMPT.format(target_language=target_lang))]
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
            
        # Find the first human query in this conversation
        initial_query = ""
        for m in state["messages"]:
            if getattr(m, "type", None) == "human" or getattr(m, "role", "") == "user":
                initial_query = getattr(m, "content", "")
                break

        final_response = state["messages"][-1].content
        
        logger.info(f"🤔 [GRAPH] Evaluating helpfulness - query: '{initial_query[:50]}...', response: '{final_response[:50]}...'")
        
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


def build_graph():
    """Compila grafo."""
    try:
        logger.info("🏗️ [GRAPH] Building agent graph...")
        
        graph = StateGraph(AgentState)
        tool_node = ToolNode(get_tool_belt())

        # Add nodes
        graph.add_node("agent", call_model)
        graph.add_node("action", tool_node)
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
