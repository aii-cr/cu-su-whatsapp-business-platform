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


class WriterAgentState(TypedDict, total=False):
    """State for the Writer Agent with helpfulness validation."""
    # Input
    user_query: str
    conversation_id: str
    
    # Processing
    messages: List[Dict[str, Any]]
    context_retrieved: bool
    information_retrieved: bool
    last_customer_message: str  # Store the last customer message for RAG
    conversation_context: str   # Store the full conversation context
    
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
    
    def _load_system_prompt(self) -> str:
        """Load the system prompt from file."""
        prompt_path = Path(__file__).parent.parent / "prompts" / "writer_system.md"
        return prompt_path.read_text(encoding="utf-8")
    
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
            "last_customer_message": "",
            "conversation_context": "",
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
    
    # Node implementations
    
    async def _start_processing(self, state: WriterAgentState) -> WriterAgentState:
        """Initialize processing and retrieve conversation context if needed."""
        state["node_history"] = state.get("node_history", []) + ["start_processing"]
        state["iteration_count"] = 0
        
        # Initialize messages with system prompt
        system_prompt = self._load_system_prompt()
        
        # Add conversation ID context to the system prompt
        conversation_context = ""
        if state.get("conversation_id"):
            conversation_context = f"\n\nIMPORTANT: The conversation ID for this request is: {state['conversation_id']}"
            conversation_context += "\nWhen using the conversation context tool, always use this exact conversation ID."
        
        state["messages"] = [
            {"role": "system", "content": system_prompt + conversation_context},
            {"role": "user", "content": state["user_query"]}
        ]
        
        # For contextual requests, immediately retrieve conversation context
        if ("current conversation context" in state["user_query"].lower() and 
            state.get("conversation_id")):
            
            logger.info("Retrieving conversation context for contextual request")
            
            # Get conversation context tool
            conversation_tool = None
            for tool in self.tools:
                if tool.name == "get_conversation_context":
                    conversation_tool = tool
                    break
            
            if conversation_tool:
                try:
                    # Retrieve conversation context
                    context_result = await conversation_tool.ainvoke({
                        "conversation_id": state["conversation_id"],
                        "include_metadata": True
                    })
                    
                    # Store the conversation context
                    state["conversation_context"] = context_result
                    state["context_retrieved"] = True
                    
                    # Extract the last customer message for RAG queries
                    last_customer_msg = self._extract_last_customer_message(context_result)
                    state["last_customer_message"] = last_customer_msg
                    
                    # Add context to messages
                    state["messages"].append({
                        "role": "user",
                        "content": f"Conversation Context:\n{context_result}"
                    })
                    
                    logger.info(f"Retrieved conversation context with {len(context_result)} characters")
                    
                except Exception as e:
                    logger.error(f"Error retrieving conversation context: {str(e)}")
                    state["messages"].append({
                        "role": "user",
                        "content": "Error: Could not retrieve conversation context. Please proceed without historical context."
                    })
        
        return state
    
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
            # Build conversation context from previous exchanges
            messages = []
            
            # Start with system message including conversation ID context
            system_prompt = self._load_system_prompt()
            if state.get("conversation_id"):
                system_prompt += f"\n\nIMPORTANT: The conversation ID for this request is: {state['conversation_id']}\nWhen using the conversation context tool, always use this exact conversation ID."
            
            messages.append(SystemMessage(content=system_prompt))
            
            # Add the initial user query
            messages.append(HumanMessage(content=state["user_query"]))
            
            # Add conversation history from tool results and responses
            for msg in state["messages"]:
                if msg["role"] == "user" and "Tool" in msg.get("content", ""):
                    # Add tool results as user messages
                    messages.append(HumanMessage(content=msg["content"]))
                elif (msg["role"] == "assistant" and 
                      msg.get("content") and 
                      not msg.get("tool_calls") and
                      "HELPFULNESS:" not in msg.get("content", "")):
                    # Add assistant responses (but not tool calls or helpfulness evals)
                    messages.append(AIMessage(content=msg["content"]))
            
            # For contextual requests, ensure we have conversation context
            if ("current conversation context" in state["user_query"].lower() and 
                not state.get("context_retrieved") and 
                state.get("conversation_id")):
                
                # Force context retrieval for contextual requests
                logger.info("Forcing conversation context retrieval for contextual request")
                state["context_retrieved"] = True
                
                # Create a direct tool call for conversation context
                fake_response = type('Response', (), {
                    'content': "I need to get the conversation context first.",
                    'tool_calls': [{
                        'name': 'get_conversation_context',
                        'args': {
                            'conversation_id': state['conversation_id'],
                            'include_metadata': True
                        }
                    }]
                })()
                
                state["messages"].append({
                    "role": "assistant", 
                    "content": fake_response.content,
                    "tool_calls": fake_response.tool_calls
                })
                
                return state
            
            # If we have context but no information retrieved yet, suggest using RAG
            if (state.get("context_retrieved") and 
                not state.get("information_retrieved") and 
                state.get("last_customer_message") and
                state["iteration_count"] == 1):
                
                # Add a hint to use RAG with the last customer message
                hint_message = f"""
Based on the conversation context, I can see the last customer message is: "{state['last_customer_message']}"

I should use the retrieve_information tool to get relevant information about what the customer is asking for.
"""
                
                state["messages"].append({
                    "role": "user",
                    "content": hint_message
                })
            
            logger.info(f"Calling model with {len(messages)} messages (iteration {state['iteration_count']})")
            
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
        """Execute tool calls with enhanced RAG query handling."""
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
                
                logger.info(f"Executing tool: {tool_name}")
                
                # Fix conversation_id for conversation context tool
                if tool_name == "get_conversation_context" and "conversation_id" in tool_args:
                    if tool_args["conversation_id"] == "current" and state.get("conversation_id"):
                        tool_args["conversation_id"] = state["conversation_id"]
                        logger.info(f"Fixed conversation_id from 'current' to '{state['conversation_id']}'")
                
                # Enhanced RAG query handling
                if tool_name == "retrieve_information":
                    # Use the last customer message for RAG queries if available
                    if state.get("last_customer_message") and tool_args.get("query"):
                        # Check if the query is too generic (like just "services")
                        current_query = tool_args["query"].strip().lower()
                        last_customer_msg = state["last_customer_message"].strip().lower()
                        
                        # If the query is too short or generic, use the last customer message
                        if (len(current_query) < 10 or 
                            current_query in ["services", "servicios", "info", "information", "help", "ayuda"]):
                            
                            # Use the full last customer message for better RAG results
                            tool_args["query"] = state["last_customer_message"]
                            logger.info(f"Enhanced RAG query from '{current_query}' to '{state['last_customer_message'][:100]}...'")
                
                # Track context retrieval
                if tool_name == "get_conversation_context":
                    state["context_retrieved"] = True
                elif tool_name in ["search_knowledge_base", "rag_search", "retrieve_information"]:
                    state["information_retrieved"] = True
                
                # Find the tool
                tool = None
                for t in self.tools:
                    if t.name == tool_name:
                        tool = t
                        break
                
                if tool:
                    try:
                        # Execute the tool
                        if hasattr(tool, 'ainvoke'):
                            result = await tool.ainvoke(tool_args)
                        else:
                            result = await tool.ainvoke(tool_args)
                        
                        # Check if tool execution failed
                        if isinstance(result, str) and "Error" in result:
                            logger.warning(f"Tool {tool_name} returned error: {result}")
                            # For failed conversation context, provide fallback
                            if tool_name == "get_conversation_context":
                                result = "Unable to retrieve conversation context. Please proceed without historical context."
                        
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
