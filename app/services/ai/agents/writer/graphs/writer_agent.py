"""
Writer Agent graph with helpfulness validation loop.
"""

from __future__ import annotations

from typing import Dict, Any, TypedDict, Literal, List
from pathlib import Path
from datetime import datetime

from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langchain_core.prompts import PromptTemplate, ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from app.core.logger import logger
from app.services.ai.config import ai_config
from app.services.ai.agents.writer.tools import get_writer_tool_belt


class WriterAgentState(TypedDict, total=False):
    """State for the Writer Agent with helpfulness validation."""
    # Input
    user_query: str
    conversation_id: str
    
    # Processing
    messages: List[Dict[str, Any]]
    context_retrieved: bool
    information_retrieved: bool
    
    # Output
    response: str
    helpfulness_score: str  # Y/N
    iteration_count: int
    
    # Metadata
    processing_start_time: str
    node_history: List[str]


class WriterAgent:
    """
    Writer Agent with helpfulness validation loop.
    Helps human agents craft better responses with iterative improvement.
    """
    
    def __init__(self, model_name: str = None):
        """Initialize the Writer Agent."""
        self.model_name = model_name or ai_config.openai_model
        
        # Initialize LLM for main generation
        self.llm = ChatOpenAI(
            openai_api_key=ai_config.openai_api_key,
            model=self.model_name,
            temperature=0.3  # Slightly more creative for writing
        )
        
        # Initialize LLM for helpfulness evaluation
        self.evaluator_llm = ChatOpenAI(
            openai_api_key=ai_config.openai_api_key,
            model="gpt-4o-mini",  # Use faster model for evaluation
            temperature=0.1
        )
        
        # Get tools
        self.tools = get_writer_tool_belt()
        self.llm_with_tools = self.llm.bind_tools(self.tools)
        
        # Build the graph
        self.graph = self._build_graph()
        
        logger.info(f"Writer Agent initialized with model: {self.model_name}")
    
    def _load_system_prompt(self) -> str:
        """Load the system prompt from file."""
        prompt_path = Path(__file__).parent.parent / "prompts" / "writer_system.md"
        return prompt_path.read_text(encoding="utf-8")
    
    def _build_graph(self) -> StateGraph:
        """Build the Writer Agent graph with helpfulness validation loop."""
        
        workflow = StateGraph(WriterAgentState)
        
        # Create tool node
        tool_node = ToolNode(self.tools)
        
        # Add nodes
        workflow.add_node("start_processing", self._start_processing)
        workflow.add_node("agent", self._call_model)
        workflow.add_node("action", tool_node)
        workflow.add_node("helpfulness", self._helpfulness_node)
        
        # Set entry point
        workflow.set_entry_point("start_processing")
        
        # Add edges
        workflow.add_edge("start_processing", "agent")
        
        # Conditional edge from agent
        workflow.add_conditional_edges(
            "agent",
            self._route_to_action_or_helpfulness,
            {
                "action": "action",
                "helpfulness": "helpfulness"
            }
        )
        
        # Action always goes back to agent
        workflow.add_edge("action", "agent")
        
        # Conditional edge from helpfulness
        workflow.add_conditional_edges(
            "helpfulness", 
            self._helpfulness_decision,
            {
                "continue": "agent",
                "end": END,
                END: END
            }
        )
        
        return workflow.compile()
    
    async def generate_response(
        self,
        user_query: str,
        conversation_id: str = None
    ) -> WriterAgentState:
        """
        Generate a response using the Writer Agent.
        
        Args:
            user_query: The human agent's request
            conversation_id: Optional conversation ID for context
            
        Returns:
            Final state with generated response
        """
        # Initialize state
        initial_state: WriterAgentState = {
            "user_query": user_query,
            "conversation_id": conversation_id or "",
            "messages": [],
            "context_retrieved": False,
            "information_retrieved": False,
            "iteration_count": 0,
            "processing_start_time": datetime.now().isoformat(),
            "node_history": []
        }
        
        logger.info(
            f"Writer Agent processing request: '{user_query[:100]}...' "
            f"for conversation: {conversation_id}"
        )
        
        try:
            # Run the graph
            final_state = await self.graph.ainvoke(initial_state)
            
            processing_time = (
                datetime.now() - datetime.fromisoformat(initial_state["processing_start_time"])
            ).total_seconds()
            
            logger.info(
                f"Writer Agent completed in {processing_time:.2f}s "
                f"(iterations: {final_state.get('iteration_count', 0)}, "
                f"nodes: {final_state.get('node_history', [])})"
            )
            
            return final_state
            
        except Exception as e:
            logger.error(f"Error in Writer Agent: {str(e)}")
            
            return {
                **initial_state,
                "response": f"Lo siento, ocurrió un error generando la respuesta: {str(e)}",
                "helpfulness_score": "N",
                "node_history": ["error"]
            }
    
    # Node implementations
    
    async def _start_processing(self, state: WriterAgentState) -> WriterAgentState:
        """Initialize processing."""
        state["node_history"] = state.get("node_history", []) + ["start_processing"]
        state["iteration_count"] = 0
        
        # Initialize messages with system prompt
        system_prompt = self._load_system_prompt()
        state["messages"] = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": state["user_query"]}
        ]
        
        return state
    
    async def _call_model(self, state: WriterAgentState) -> WriterAgentState:
        """Call the model with current messages."""
        state["node_history"] = state.get("node_history", []) + ["agent"]
        state["iteration_count"] = state.get("iteration_count", 0) + 1
        
        # Convert messages to LangChain format
        messages = []
        for msg in state["messages"]:
            if msg["role"] == "system":
                messages.append(SystemMessage(content=msg["content"]))
            elif msg["role"] == "user":
                messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                messages.append(AIMessage(content=msg["content"]))
        
        # Call model with tools
        response = await self.llm_with_tools.ainvoke(messages)
        
        # Add response to messages
        state["messages"].append({
            "role": "assistant", 
            "content": response.content,
            "tool_calls": getattr(response, "tool_calls", [])
        })
        
        return state
    
    def _route_to_action_or_helpfulness(self, state: WriterAgentState) -> str:
        """Route to tools or helpfulness evaluation."""
        last_message = state["messages"][-1]
        
        # Check if there are tool calls
        if last_message.get("tool_calls"):
            return "action"
        
        # No tool calls, go to helpfulness evaluation
        return "helpfulness"
    
    async def _helpfulness_node(self, state: WriterAgentState) -> WriterAgentState:
        """Evaluate helpfulness of the response."""
        state["node_history"] = state.get("node_history", []) + ["helpfulness"]
        
        # Guard against infinite loops
        if state.get("iteration_count", 0) > 5:
            logger.warning("Writer Agent hit max iterations, ending loop")
            state["messages"].append({
                "role": "assistant",
                "content": "HELPFULNESS:END"
            })
            return state
        
        # Get initial query and final response
        initial_query = state["user_query"]
        last_response = None
        
        # Find the last actual response (not tool calls)
        for msg in reversed(state["messages"]):
            if (msg["role"] == "assistant" and 
                not msg.get("tool_calls") and 
                "HELPFULNESS:" not in msg["content"]):
                last_response = msg["content"]
                break
        
        if not last_response:
            # No response yet, continue
            state["messages"].append({
                "role": "assistant",
                "content": "HELPFULNESS:N"
            })
            return state
        
        # Create helpfulness evaluation prompt
        helpfulness_prompt = """
Given a human agent's request and the AI's response, evaluate if the response is extremely helpful and ready to send to a customer.

Consider:
1. Does it directly address the request?
2. Is it well-written and professional?
3. Is it appropriate for WhatsApp Business communication?
4. Does it provide actionable information?
5. Is the tone appropriate for customer service?

Respond with 'Y' if the response is excellent and ready to use, or 'N' if it needs improvement.

Human Agent Request:
{initial_query}

AI Response:
{final_response}

Evaluation (Y/N):"""
        
        # Call evaluator model
        prompt = PromptTemplate.from_template(helpfulness_prompt)
        evaluation_chain = prompt | self.evaluator_llm | StrOutputParser()
        
        try:
            helpfulness_response = await evaluation_chain.ainvoke({
                "initial_query": initial_query,
                "final_response": last_response
            })
            
            # Extract decision
            decision = "Y" if "Y" in helpfulness_response.upper() else "N"
            
            logger.info(
                f"Helpfulness evaluation: {decision} for iteration {state.get('iteration_count', 0)}"
            )
            
            # Add evaluation to messages
            state["messages"].append({
                "role": "assistant",
                "content": f"HELPFULNESS:{decision}"
            })
            
            # Store the actual response for final output
            if decision == "Y":
                state["response"] = last_response
                state["helpfulness_score"] = "Y"
            else:
                # Add feedback for improvement
                state["messages"].append({
                    "role": "user",
                    "content": (
                        "The response needs improvement. Please revise it to be more helpful, "
                        "professional, and appropriate for customer service. Consider using "
                        "available tools to get more relevant information if needed."
                    )
                })
            
        except Exception as e:
            logger.error(f"Error in helpfulness evaluation: {str(e)}")
            # Default to continuing if evaluation fails
            state["messages"].append({
                "role": "assistant", 
                "content": "HELPFULNESS:N"
            })
        
        return state
    
    def _helpfulness_decision(self, state: WriterAgentState) -> str:
        """Decide whether to continue or end based on helpfulness."""
        # Check for loop limit marker
        if any("HELPFULNESS:END" in msg.get("content", "") 
               for msg in state["messages"][-1:]):
            return END
        
        # Check last helpfulness evaluation
        last_message = state["messages"][-1]
        content = last_message.get("content", "")
        
        if "HELPFULNESS:Y" in content:
            return "end"
        else:
            return "continue"
    
    async def health_check(self) -> Dict[str, Any]:
        """Check Writer Agent health."""
        try:
            # Test a simple query
            test_result = await self.generate_response(
                user_query="Test query for health check",
                conversation_id=None
            )
            
            return {
                "status": "healthy",
                "model": self.model_name,
                "tools_count": len(self.tools),
                "test_iterations": test_result.get("iteration_count", 0),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Writer Agent health check failed: {str(e)}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
