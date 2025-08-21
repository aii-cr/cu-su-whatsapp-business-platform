"""
Main WhatsApp agent using LangGraph for state management and flow control.
Implements typed state with explicit nodes and conditional edges.
"""

import asyncio
from typing import TypedDict, Literal, Dict, Any, List, Optional
from datetime import datetime

from langgraph.graph import StateGraph, END
from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI

from app.core.logger import logger
from app.services.ai.config import ai_config
from app.services.ai.tools.rag_tool import RAGTool
from app.services.ai.graphs.subgraphs.faq_rag_flow import run_rag_flow
from app.services.ai.graphs.subgraphs.language_detection import detect_language_and_greeting


class AgentState(TypedDict, total=False):
    """
    Typed state for the WhatsApp agent.
    All fields are optional (total=False) to allow partial updates.
    """
    # Input
    user_text: str
    conversation_id: str
    customer_phone: str
    message_id: str
    
    # Processing state
    intent: Literal["faq", "booking", "payment", "fallback", "greeting"]
    customer_language: str
    is_first_message: bool
    ai_autoreply_enabled: bool
    
    # RAG context
    context_docs: List[Dict[str, Any]]
    tool_result: Dict[str, Any]
    
    # Output
    reply: str
    confidence: float
    requires_human_handoff: bool
    
    # Metadata
    processing_start_time: str
    node_history: List[str]


class WhatsAppAgent:
    """
    Main WhatsApp agent using LangGraph for conversation flow.
    Handles intent detection, RAG retrieval, and response generation.
    """
    
    def __init__(self, model_name: str = None):
        """
        Initialize the WhatsApp agent.
        
        Args:
            model_name: OpenAI model name (defaults to config)
        """
        self.model_name = model_name or ai_config.openai_model
        
        # Initialize LLM
        self.llm = ChatOpenAI(
            openai_api_key=ai_config.openai_api_key,
            model=self.model_name,
            temperature=0.1
        )
        
        # Initialize tools
        self.rag_tool = RAGTool()
        
        # Build the graph
        self.graph = self._build_graph()
        
        logger.info(f"WhatsApp agent initialized with model: {self.model_name}")
    
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph state machine."""
        
        # Create the graph
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("start_processing", self._start_processing)
        workflow.add_node("detect_language", detect_language_and_greeting)
        workflow.add_node("detect_intent", self._detect_intent)
        workflow.add_node("check_autoreply", self._check_autoreply)
        workflow.add_node("faq_rag", run_rag_flow)
        workflow.add_node("booking_flow", self._booking_flow)
        workflow.add_node("payment_flow", self._payment_flow)
        workflow.add_node("fallback_flow", self._fallback_flow)
        workflow.add_node("finalize_response", self._finalize_response)
        
        # Set entry point
        workflow.set_entry_point("start_processing")
        
        # Add edges
        workflow.add_edge("start_processing", "detect_language")
        workflow.add_edge("detect_language", "check_autoreply")
        
        # Conditional edge from check_autoreply
        workflow.add_conditional_edges(
            "check_autoreply",
            self._should_process,
            {
                "continue": "detect_intent",
                "stop": END
            }
        )
        
        workflow.add_conditional_edges(
            "detect_intent",
            self._route_by_intent,
            {
                "faq": "faq_rag",
                "booking": "booking_flow", 
                "payment": "payment_flow",
                "fallback": "fallback_flow"
            }
        )
        
        # All intent flows go to finalize
        workflow.add_edge("faq_rag", "finalize_response")
        workflow.add_edge("booking_flow", "finalize_response")
        workflow.add_edge("payment_flow", "finalize_response")
        workflow.add_edge("fallback_flow", "finalize_response")
        
        workflow.add_edge("finalize_response", END)
        
        # Compile the graph
        return workflow.compile()
    
    async def process_message(
        self,
        user_text: str,
        conversation_id: str,
        customer_phone: str,
        message_id: str,
        ai_autoreply_enabled: bool = True,
        is_first_message: bool = False
    ) -> AgentState:
        """
        Process a WhatsApp message through the agent graph.
        
        Args:
            user_text: Customer message text
            conversation_id: Conversation identifier
            customer_phone: Customer phone number
            message_id: Message identifier
            ai_autoreply_enabled: Whether auto-reply is enabled
            is_first_message: Whether this is the first message
            
        Returns:
            Final agent state with response
        """
        # Initialize state
        initial_state: AgentState = {
            "user_text": user_text,
            "conversation_id": conversation_id,
            "customer_phone": customer_phone,
            "message_id": message_id,
            "ai_autoreply_enabled": ai_autoreply_enabled,
            "is_first_message": is_first_message,
            "processing_start_time": datetime.now().isoformat(),
            "node_history": []
        }
        
        logger.info(f"Processing message for conversation {conversation_id}: '{user_text[:100]}...'")
        
        try:
            # Run the graph
            final_state = await self.graph.ainvoke(initial_state)
            
            processing_time = (
                datetime.now() - datetime.fromisoformat(initial_state["processing_start_time"])
            ).total_seconds()
            
            logger.info(
                f"Agent processing completed in {processing_time:.2f}s "
                f"(conversation: {conversation_id}, nodes: {final_state.get('node_history', [])})"
            )
            
            return final_state
            
        except Exception as e:
            logger.error(f"Error in agent processing: {str(e)}")
            
            # Return error state
            return {
                **initial_state,
                "reply": "Lo siento, ocurrió un error procesando tu mensaje. Un agente te contactará pronto.",
                "confidence": 0.0,
                "requires_human_handoff": True,
                "node_history": ["error"]
            }
    
    # Node implementations
    
    async def _start_processing(self, state: AgentState) -> AgentState:
        """Initialize processing and add to node history."""
        state["node_history"] = state.get("node_history", []) + ["start_processing"]
        logger.info(f"Starting processing for conversation {state['conversation_id']}")
        return state
    
    async def _detect_intent(self, state: AgentState) -> AgentState:
        """Detect user intent from the message."""
        state["node_history"] = state.get("node_history", []) + ["detect_intent"]
        
        user_text = state["user_text"].lower()
        
        # Simple keyword-based intent detection
        # In production, you might use a more sophisticated classifier
        
        booking_keywords = [
            "reserva", "reservar", "booking", "book", "cita", "appointment",
            "disponibilidad", "availability", "horario", "schedule"
        ]
        
        payment_keywords = [
            "pago", "pagar", "payment", "pay", "precio", "price", "cost",
            "tarjeta", "card", "transfer", "paypal"
        ]
        
        if any(keyword in user_text for keyword in booking_keywords):
            state["intent"] = "booking"
        elif any(keyword in user_text for keyword in payment_keywords):
            state["intent"] = "payment"
        else:
            state["intent"] = "faq"  # Default to FAQ/information
        
        logger.info(f"Detected intent: {state['intent']} for message: '{user_text[:50]}...'")
        return state
    
    async def _check_autoreply(self, state: AgentState) -> AgentState:
        """Check if auto-reply is enabled."""
        state["node_history"] = state.get("node_history", []) + ["check_autoreply"]
        
        if not state.get("ai_autoreply_enabled", True):
            logger.info(f"Auto-reply disabled for conversation {state['conversation_id']}")
            state["reply"] = "NO_REPLY"
            state["requires_human_handoff"] = True
            
        return state
    
    async def _booking_flow(self, state: AgentState) -> AgentState:
        """Handle booking-related queries."""
        state["node_history"] = state.get("node_history", []) + ["booking_flow"]
        
        # For now, use RAG to answer booking questions
        # In future, this could integrate with booking systems
        rag_result = await self.rag_tool.execute_with_timeout(
            query=state["user_text"],
            tenant_id="default",
            locale=state.get("customer_language", "es")
        )
        
        if rag_result.status == "success":
            state["reply"] = rag_result.data["answer"]
            state["confidence"] = rag_result.data["confidence"]
            state["tool_result"] = rag_result.data
        else:
            state["reply"] = "Lo siento, no puedo ayudarte con reservas en este momento. Te conectaré con un agente."
            state["confidence"] = 0.0
            state["requires_human_handoff"] = True
        
        return state
    
    async def _payment_flow(self, state: AgentState) -> AgentState:
        """Handle payment-related queries."""
        state["node_history"] = state.get("node_history", []) + ["payment_flow"]
        
        # For now, use RAG to answer payment questions
        # In future, this could integrate with payment systems
        rag_result = await self.rag_tool.execute_with_timeout(
            query=state["user_text"],
            tenant_id="default", 
            locale=state.get("customer_language", "es")
        )
        
        if rag_result.status == "success":
            state["reply"] = rag_result.data["answer"]
            state["confidence"] = rag_result.data["confidence"]
            state["tool_result"] = rag_result.data
        else:
            state["reply"] = "Lo siento, no puedo ayudarte con pagos en este momento. Te conectaré con un agente."
            state["confidence"] = 0.0
            state["requires_human_handoff"] = True
        
        return state
    
    async def _fallback_flow(self, state: AgentState) -> AgentState:
        """Handle fallback cases."""
        state["node_history"] = state.get("node_history", []) + ["fallback_flow"]
        
        state["reply"] = "Lo siento, no entendí tu consulta. Te conectaré con un agente humano."
        state["confidence"] = 0.0
        state["requires_human_handoff"] = True
        
        return state
    
    async def _finalize_response(self, state: AgentState) -> AgentState:
        """Finalize the response and add metadata."""
        state["node_history"] = state.get("node_history", []) + ["finalize_response"]
        
        # Add greeting if first message
        if state.get("is_first_message") and state.get("reply") != "NO_REPLY":
            greeting = self._get_greeting(state.get("customer_language", "es"))
            state["reply"] = f"{greeting}\n\n{state.get('reply', '')}"
        
        # Ensure confidence is set
        if "confidence" not in state:
            state["confidence"] = 0.5
        
        # Set handoff flag based on confidence
        if state["confidence"] < ai_config.confidence_threshold:
            state["requires_human_handoff"] = True
        
        # Truncate response if too long
        if len(state.get("reply", "")) > ai_config.max_response_length:
            state["reply"] = state["reply"][:ai_config.max_response_length - 3] + "..."
        
        logger.info(
            f"Finalized response for conversation {state['conversation_id']}: "
            f"confidence={state['confidence']}, handoff={state.get('requires_human_handoff', False)}"
        )
        
        return state
    
    def _get_greeting(self, language: str) -> str:
        """Get appropriate greeting based on language."""
        if language == "en":
            return "Hi there! 👋 How can I help you today?"
        else:  # Default to Spanish
            return "¡Hola! 👋 ¿En qué puedo ayudarte?"
    
    # Conditional edge functions
    
    def _should_process(self, state: AgentState) -> str:
        """Determine if processing should continue."""
        if state.get("ai_autoreply_enabled", True):
            return "continue"
        else:
            return "stop"
    
    def _route_by_intent(self, state: AgentState) -> str:
        """Route to appropriate flow based on intent."""
        intent = state.get("intent", "fallback")
        
        if intent in ["faq", "booking", "payment", "fallback"]:
            return intent
        else:
            return "fallback"
    
    async def health_check(self) -> Dict[str, Any]:
        """Check agent health and dependencies."""
        try:
            # Test RAG tool
            rag_health = await self.rag_tool.execute_with_timeout(
                query="test query",
                tenant_id="default",
                locale="es"
            )
            
            return {
                "status": "healthy",
                "model": self.model_name,
                "rag_tool_status": rag_health.status,
                "graph_nodes": len(self.graph.nodes),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Agent health check failed: {str(e)}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
