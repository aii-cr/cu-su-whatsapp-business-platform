"""
Writer Agent graph with helpfulness validation loop and LangSmith tracing.
"""

from __future__ import annotations

from typing import Dict, Any, TypedDict, Literal, List
from pathlib import Path
from datetime import datetime
import re

from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langchain_core.prompts import PromptTemplate, ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from app.core.logger import logger
from app.services.ai.config import ai_config
from app.services.ai.agents.writer.tools import get_writer_tool_belt
from app.services.ai.agents.writer.telemetry import setup_tracing
from app.services.ai.agents.writer.prompts.prompts import (
    PREBUILT_CHAT_PROMPT,
    CUSTOM_CHAT_PROMPT
)


class WriterAgentState(TypedDict, total=False):
    """State for the Writer Agent with helpfulness validation."""
    # Input
    user_query: str
    conversation_id: str
    mode: str  # "prebuilt" or "custom"
    
    # Processing
    messages: List[Dict[str, Any]]
    context_retrieved: bool
    information_retrieved: bool
    last_customer_message: str  # Store the last customer message for RAG
    conversation_context: str   # Store the full conversation context
    customer_name: str  # Extracted customer name
    
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
        """Initialize the Writer Agent with LangSmith tracing."""
        # Setup LangSmith tracing first
        setup_tracing()
        
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
        
        logger.info(f"Writer Agent initialized with model: {self.model_name} (LangSmith tracing enabled)")
    
    def _get_chat_prompt_template(self, mode: str):
        """Get the appropriate ChatPromptTemplate based on mode."""
        if mode == "prebuilt":
            return PREBUILT_CHAT_PROMPT
        else:
            return CUSTOM_CHAT_PROMPT
    
    def _build_graph(self) -> StateGraph:
        """Build the Writer Agent graph with helpfulness validation loop."""
        
        workflow = StateGraph(WriterAgentState)
        
        # Create tool node
        tool_node = ToolNode(self.tools)
        
        # Add custom action node for debugging
        workflow.add_node("action", self._action_node)
        
        # Add nodes
        workflow.add_node("start_processing", self._start_processing)
        workflow.add_node("agent", self._call_model)
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
        
        # Compile the graph
        return workflow.compile()
    
    async def generate_response(
        self,
        user_query: str,
        conversation_id: str = None,
        mode: str = "custom"
    ) -> WriterAgentState:
        """
        Generate a response using the Writer Agent.
        
        Args:
            user_query: The human agent's request or customer query
            conversation_id: Optional conversation ID for context
            mode: "prebuilt" for contextual responses, "custom" for agent requests
            
        Returns:
            Final state with generated response
        """
        # Initialize state
        initial_state: WriterAgentState = {
            "user_query": user_query,
            "conversation_id": conversation_id or "",
            "mode": mode,
            "messages": [],
            "context_retrieved": False,
            "information_retrieved": False,
            "last_customer_message": "",
            "conversation_context": "",
            "customer_name": "",
            "iteration_count": 0,
            "processing_start_time": datetime.now().isoformat(),
            "node_history": []
        }
        
        logger.info(
            f"Writer Agent processing request: '{user_query[:100]}...' "
            f"for conversation: {conversation_id}"
        )
        
        try:
            # Run the graph with timeout protection and recursion limit
            import asyncio
            
            # Set a timeout for the entire operation
            final_state = await asyncio.wait_for(
                self.graph.ainvoke(
                    initial_state,
                    config={"recursion_limit": 15}  # Reduced recursion limit
                ),
                timeout=30.0  # Increased timeout to 30 seconds
            )
            
            processing_time = (
                datetime.now() - datetime.fromisoformat(initial_state["processing_start_time"])
            ).total_seconds()
            
            logger.info(
                f"Writer Agent completed in {processing_time:.2f}s "
                f"(iterations: {final_state.get('iteration_count', 0)}, "
                f"nodes: {final_state.get('node_history', [])})"
            )
            
            return final_state
            
        except asyncio.TimeoutError:
            logger.error("Writer Agent timed out after 30 seconds")
            return {
                **initial_state,
                "response": "",
                "helpfulness_score": "N",
                "node_history": ["timeout"],
                "error": "Error generating response: Operation timed out"
            }
        except Exception as e:
            logger.error(f"Error in Writer Agent: {str(e)}")
            
            return {
                **initial_state,
                "response": "",
                "helpfulness_score": "N",
                "node_history": ["error"],
                "error": f"Error generating response: {str(e)}"
            }
    
    def _extract_last_customer_message(self, conversation_context: str) -> str:
        """
        Extract the last customer message from conversation context.
        
        Args:
            conversation_context: The full conversation context string
            
        Returns:
            The last customer message or empty string if not found
        """
        try:
            # First, look for the "LAST CUSTOMER MESSAGE" section
            if "=== LAST CUSTOMER MESSAGE ===" in conversation_context:
                lines = conversation_context.split('\n')
                for i, line in enumerate(lines):
                    if "=== LAST CUSTOMER MESSAGE ===" in line:
                        # Get the next line which should contain the message
                        if i + 1 < len(lines):
                            message_line = lines[i + 1].strip()
                            if message_line.startswith("Customer: "):
                                message = message_line.replace("Customer: ", "").strip()
                                if message:
                                    logger.info(f"Extracted last customer message from section: '{message[:100]}...'")
                                    return message
            
            # Fallback: Split by lines and look for the last customer message
            lines = conversation_context.split('\n')
            customer_messages = []
            
            for line in lines:
                # Look for lines that start with customer indicators
                if any(indicator in line for indicator in ['Customer:', 'Cliente:']):
                    # Extract the message content after the colon
                    if ':' in line:
                        message = line.split(':', 1)[1].strip()
                        if message:
                            customer_messages.append(message)
            
            # Return the last customer message
            if customer_messages:
                last_message = customer_messages[-1]
                logger.info(f"Extracted last customer message from history: '{last_message[:100]}...'")
                return last_message
            
            return ""
            
        except Exception as e:
            logger.error(f"Error extracting last customer message: {str(e)}")
            return ""
    
    def _extract_customer_name_from_context(self, conversation_context: str) -> str:
        """
        Extract customer name from conversation context.
        Simple extraction logic for real customer names.
        """
        if not conversation_context:
            return ""
        
        try:
            lines = conversation_context.split('\n')
            
            # Look for customer name in structured format
            for line in lines:
                line = line.strip()
                if line.startswith("Customer: ") or line.startswith("Cliente: "):
                    # Extract potential name from the beginning of the message
                    message_part = line.split(": ", 1)[1] if ": " in line else ""
                    words = message_part.split()
                    if words and len(words[0]) > 1:
                        potential_name = words[0].strip(".,!?")
                        if self._is_valid_customer_name(potential_name):
                            return potential_name
            
            return ""
            
        except Exception as e:
            logger.error(f"Error extracting customer name: {str(e)}")
            return ""
    
    def _is_valid_customer_name(self, name: str) -> bool:
        """Validate if a name appears to be a real customer name."""
        if not name or len(name.strip()) == 0:
            return False
        
        name_lower = name.lower().strip()
        
        # List of invalid name patterns
        invalid_patterns = [
            "user", "cliente", "admin", "techsupport", "whatsapp", "bot", "system",
            "test", "demo", "sample", "example", "null", "undefined", "unknown",
            "customer", "support", "help", "info", "contact"
        ]
        
        # Check if it's just numbers
        if name.strip().isdigit():
            return False
        
        # Check if it's too short (likely a username)
        if len(name.strip()) < 2:
            return False
        
        # Check if it contains obvious invalid patterns
        for pattern in invalid_patterns:
            if pattern in name_lower:
                return False
        
        # Check if it's mostly numbers with few letters (like User123)
        digit_count = sum(c.isdigit() for c in name)
        if len(name) > 0 and digit_count / len(name) > 0.7:
            return False
        
        return True
    
    # Node implementations
    
    async def _start_processing(self, state: WriterAgentState) -> WriterAgentState:
        """Initialize processing and create proper LangChain prompt."""
        state["node_history"] = state.get("node_history", []) + ["start_processing"]
        state["iteration_count"] = 0
        
        mode = state.get("mode", "custom")
        conversation_id = state.get("conversation_id")
        user_query = state["user_query"]
        
        logger.info(f"Starting processing in {mode} mode with query: '{user_query[:100]}...'")
        
        # Always retrieve conversation context if conversation_id is provided
        conversation_context = ""
        if conversation_id:
            await self._retrieve_conversation_context(state)
            conversation_context = state.get("conversation_context", "")
        
        # Determine the correct query and context based on mode
        if mode == "prebuilt":
            # Prebuilt mode: use last customer message as query
            query = state.get("last_customer_message", user_query)
            context = f"Conversation Context:\n{conversation_context}" if conversation_context else "No conversation context available."
            logger.info(f"Prebuilt mode: using last customer message as query: '{query[:100]}...'")
        else:
            # Custom mode: use user query as query (this is the FIX!)
            query = user_query
            context = f"Conversation Context (for reference):\n{conversation_context}" if conversation_context else "No conversation context provided."
            logger.info(f"Custom mode: using user query as query: '{query[:100]}...'")
        
        # Get the appropriate chat prompt template
        chat_prompt = self._get_chat_prompt_template(mode)
        
        # Format the prompt with the correct parameters
        formatted_messages = chat_prompt.format_messages(
            query=query,
            context=context
        )
        
        # Convert to the format expected by our message handling
        state["messages"] = []
        for msg in formatted_messages:
            if hasattr(msg, 'type'):
                if msg.type == "system":
                    state["messages"].append({"role": "system", "content": msg.content})
                elif msg.type == "human":
                    state["messages"].append({"role": "user", "content": msg.content})
                elif msg.type == "ai":
                    state["messages"].append({"role": "assistant", "content": msg.content})
        
        logger.info(f"Initialized {mode} mode with conversation context: {bool(conversation_context)}")
        logger.info(f"Generated {len(state['messages'])} messages for LLM")
        
        return state
    
    async def _retrieve_conversation_context(self, state: WriterAgentState) -> None:
        """Retrieve conversation context and extract relevant information."""
        conversation_id = state.get("conversation_id")
        if not conversation_id:
            return
        
        logger.info(f"Retrieving conversation context for conversation: {conversation_id}")
        
        # Get conversation context tool
        conversation_tool = None
        for tool in self.tools:
            if tool.name == "get_conversation_context":
                conversation_tool = tool
                break
        
        if not conversation_tool:
            logger.warning("Conversation context tool not found")
            return
        
        try:
            # Retrieve conversation context
            context_result = await conversation_tool.ainvoke({
                "conversation_id": conversation_id,
                "include_metadata": True
            })
            
            # Store the conversation context
            state["conversation_context"] = context_result
            state["context_retrieved"] = True
            
            # Extract the last customer message
            last_customer_msg = self._extract_last_customer_message(context_result)
            state["last_customer_message"] = last_customer_msg
            
            # Extract customer name (simple extraction)
            customer_name = self._extract_customer_name_from_context(context_result)
            if customer_name:
                state["customer_name"] = customer_name
            
            logger.info(f"Retrieved conversation context: {len(context_result)} chars, last message: '{last_customer_msg[:50]}...', customer: {customer_name or 'N/A'}")
            
        except Exception as e:
            logger.error(f"Error retrieving conversation context: {str(e)}")
            state["conversation_context"] = "Error: Could not retrieve conversation context."
    
    async def _call_model(self, state: WriterAgentState) -> WriterAgentState:
        """Call the model with current messages."""
        state["node_history"] = state.get("node_history", []) + ["agent"]
        state["iteration_count"] = state.get("iteration_count", 0) + 1
        
        # Check for max iterations to prevent infinite loops
        if state["iteration_count"] > 5:
            logger.warning(f"Max iterations reached ({state['iteration_count']}), forcing completion")
            state["messages"].append({
                "role": "assistant",
                "content": "I understand you need a response for this conversation. Based on the context available, I recommend reviewing the conversation history and crafting a response that addresses the customer's most recent concern or question."
            })
            return state
        
        try:
            # Build conversation from state messages
            messages = []
            
            # Convert state messages to LangChain message objects
            for msg in state["messages"]:
                if msg["role"] == "system":
                    messages.append(SystemMessage(content=msg["content"]))
                elif msg["role"] == "user":
                    messages.append(HumanMessage(content=msg["content"]))
                elif (msg["role"] == "assistant" and 
                      msg.get("content") and 
                      not msg.get("tool_calls") and
                      "HELPFULNESS:" not in msg.get("content", "")):
                    # Add assistant responses (but not tool calls or helpfulness evals)
                    messages.append(AIMessage(content=msg["content"]))
            
            logger.info(f"Calling model with {len(messages)} messages (iteration {state['iteration_count']}, mode: {state.get('mode', 'unknown')})")
            
            # Call model with tools
            response = await self.llm_with_tools.ainvoke(messages)
            
            # Add response to messages
            state["messages"].append({
                "role": "assistant", 
                "content": response.content,
                "tool_calls": getattr(response, "tool_calls", [])
            })
            
        except Exception as e:
            logger.error(f"Error in _call_model: {str(e)}")
            # Add a fallback response
            state["messages"].append({
                "role": "assistant",
                "content": "I apologize, but I encountered an error while processing your request. Please try again."
            })
        
        return state
    
    async def _action_node(self, state: WriterAgentState) -> WriterAgentState:
        """Execute tool calls."""
        state["node_history"] = state.get("node_history", []) + ["action"]
        
        try:
            last_message = state["messages"][-1]
            tool_calls = last_message.get("tool_calls", [])
            
            if not tool_calls:
                logger.warning("Action node called but no tool calls found")
                return state
            
            for tool_call in tool_calls:
                tool_name = tool_call.get("name")
                tool_args = tool_call.get("args", {})
                
                logger.info(f"Executing tool: {tool_name} in {state.get('mode', 'unknown')} mode")
                
                # Fix conversation_id for conversation context tool
                if tool_name == "get_conversation_context" and "conversation_id" in tool_args:
                    if tool_args["conversation_id"] == "current" and state.get("conversation_id"):
                        tool_args["conversation_id"] = state["conversation_id"]
                        logger.info(f"Fixed conversation_id from 'current' to '{state['conversation_id']}'")
                
                # Track tool usage
                if tool_name == "get_conversation_context":
                    state["context_retrieved"] = True
                elif tool_name in ["search_knowledge_base", "rag_search", "retrieve_information"]:
                    state["information_retrieved"] = True
                
                # Find and execute the tool
                tool = None
                for t in self.tools:
                    if t.name == tool_name:
                        tool = t
                        break
                
                if tool:
                    try:
                        # Execute the tool
                        result = await tool.ainvoke(tool_args)
                        
                        # Check if tool execution failed
                        if isinstance(result, str) and "Error" in result:
                            logger.warning(f"Tool {tool_name} returned error: {result}")
                        
                        # Add tool result to messages
                        state["messages"].append({
                            "role": "user",
                            "content": f"Tool {tool_name} result: {result}"
                        })
                        
                    except Exception as tool_error:
                        logger.error(f"Error executing tool {tool_name}: {str(tool_error)}")
                        state["messages"].append({
                            "role": "user",
                            "content": f"Tool {tool_name} failed: {str(tool_error)}"
                        })
                else:
                    logger.warning(f"Tool {tool_name} not found")
                    state["messages"].append({
                        "role": "user",
                        "content": f"Tool {tool_name} not found"
                    })
            
        except Exception as e:
            logger.error(f"Error in action node: {str(e)}")
            state["messages"].append({
                "role": "user",
                "content": f"Error executing tools: {str(e)}"
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
        
        # Guard against infinite loops - increased threshold for better responses
        if state.get("iteration_count", 0) > 3:
            logger.warning("Writer Agent hit max iterations (3), ending loop")
            
            # Try to extract the best response we have so far
            best_response = None
            for msg in reversed(state["messages"]):
                if (msg["role"] == "assistant" and 
                    not msg.get("tool_calls") and 
                    "HELPFULNESS:" not in msg.get("content", "") and
                    msg.get("content", "").strip()):
                    best_response = msg["content"]
                    break
            
            if best_response:
                state["response"] = best_response
                state["helpfulness_score"] = "Y"  # Accept what we have
            
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
