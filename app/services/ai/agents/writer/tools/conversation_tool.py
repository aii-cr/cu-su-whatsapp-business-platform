"""
Conversation context tool for the Writer Agent.
Retrieves full conversation history for context analysis.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime

from langchain.tools import StructuredTool
from pydantic import BaseModel, Field

from app.core.logger import logger
from app.services.ai.shared.base_tools import BaseAgentTool, ToolResult
from app.db.client import database


class ConversationContextInput(BaseModel):
    """Input schema for conversation context tool."""
    conversation_id: str = Field(..., description="The conversation ID to retrieve context for")
    include_metadata: bool = Field(default=True, description="Whether to include message metadata")


class ConversationContextTool(BaseAgentTool):
    """Tool to retrieve full conversation context for analysis."""
    
    name: str = "get_conversation_context"
    description: str = """
    Retrieves the complete conversation history for a given conversation ID.
    This includes all inbound and outbound messages, timestamps, and metadata
    that can help understand the conversation flow and context.
    """
    
    async def _arun(
        self, 
        conversation_id: str,
        include_metadata: bool = True,
        run_manager=None
    ) -> str:
        """
        Retrieve conversation context.
        
        Args:
            conversation_id: The conversation ID to retrieve
            include_metadata: Whether to include message metadata
            
        Returns:
            Formatted conversation context as string
        """
        self._log_usage(conversation_id=conversation_id, include_metadata=include_metadata)
        
        try:
            # Get database instance
            db = await database.get_database()
            
            # Get conversations collection
            conversations_collection = db.conversations
            
            # Convert conversation_id to ObjectId if it's a string
            from bson import ObjectId
            if isinstance(conversation_id, str):
                try:
                    conversation_id_obj = ObjectId(conversation_id)
                except Exception as e:
                    return f"Error: Invalid conversation ID format: {conversation_id}"
            else:
                conversation_id_obj = conversation_id
            
            # Fetch the conversation
            conversation = await conversations_collection.find_one({"_id": conversation_id_obj})
            
            if not conversation:
                return f"Error: Conversation {conversation_id} not found"
            
            # Get messages collection
            messages_collection = db.messages
            
            # Fetch all messages for this conversation, ordered by timestamp
            messages_cursor = messages_collection.find(
                {"conversation_id": conversation_id_obj}
            ).sort("timestamp", 1)
            
            messages = await messages_cursor.to_list(length=None)
            
            # Format the conversation context
            context_lines = []
            
            # Add conversation metadata
            if include_metadata:
                context_lines.append("=== CONVERSATION METADATA ===")
                context_lines.append(f"Conversation ID: {conversation_id}")
                context_lines.append(f"Status: {conversation.get('status', 'unknown')}")
                context_lines.append(f"Customer Phone: {conversation.get('customer_phone', 'unknown')}")
                context_lines.append(f"Customer Name: {conversation.get('customer_name', 'unknown')}")
                context_lines.append(f"Customer Type: {conversation.get('customer_type', 'unknown')}")
                context_lines.append(f"Department: {conversation.get('department_name', 'unknown')}")
                context_lines.append(f"Total Messages: {len(messages)}")
                
                if conversation.get('created_at'):
                    context_lines.append(f"Started: {conversation['created_at']}")
                
                if conversation.get('updated_at'):
                    context_lines.append(f"Last Activity: {conversation['updated_at']}")
                
                # Add sentiment info if available
                if conversation.get('current_sentiment_emoji'):
                    sentiment_info = f"Customer Sentiment: {conversation['current_sentiment_emoji']}"
                    if conversation.get('sentiment_confidence'):
                        sentiment_info += f" ({conversation['sentiment_confidence']:.0%} confidence)"
                    context_lines.append(sentiment_info)
                
                context_lines.append("")
            
            # Add message history
            context_lines.append("=== MESSAGE HISTORY ===")
            
            for i, msg in enumerate(messages, 1):
                # Format timestamp
                timestamp = msg.get('timestamp', datetime.now())
                if isinstance(timestamp, str):
                    timestamp_str = timestamp
                else:
                    timestamp_str = timestamp.strftime("%Y-%m-%d %H:%M:%S")
                
                # Determine message type and author
                msg_type = msg.get('type', 'unknown')
                direction = msg.get('direction', 'unknown')
                
                if direction == 'inbound':
                    author = "Customer"
                elif direction == 'outbound':
                    author = msg.get('sender_name', 'Agent')
                    if msg.get('is_ai_generated', False):
                        author += " (AI)"
                else:
                    author = "System"
                
                # Message content
                content = msg.get('text_content', msg.get('text', msg.get('content', '')))
                
                # Add message with metadata
                if include_metadata:
                    context_lines.append(f"[{i:02d}] [{timestamp_str}] {author}: {content}")
                    
                    # Add delivery status if available
                    if msg.get('status'):
                        context_lines.append(f"     Status: {msg['status']}")
                    
                    # Add message type if not text
                    if msg_type != 'text' and msg_type != 'unknown':
                        context_lines.append(f"     Type: {msg_type}")
                        
                        # Add media info if available
                        if msg.get('media_url'):
                            context_lines.append(f"     Media: {msg['media_url']}")
                
                else:
                    # Simplified format without metadata
                    context_lines.append(f"{author}: {content}")
                
                context_lines.append("")  # Empty line between messages
            
            # Add summary
            context_lines.append("=== CONVERSATION ANALYSIS ===")
            
            # Count message types
            inbound_count = sum(1 for msg in messages if msg.get('direction') == 'inbound')
            outbound_count = sum(1 for msg in messages if msg.get('direction') == 'outbound')
            ai_count = sum(1 for msg in messages if msg.get('is_ai_generated', False))
            
            context_lines.append(f"Messages Breakdown:")
            context_lines.append(f"- Customer messages: {inbound_count}")
            context_lines.append(f"- Agent responses: {outbound_count}")
            context_lines.append(f"- AI generated responses: {ai_count}")
            
            # Conversation flow analysis
            context_lines.append("")
            context_lines.append("=== CONVERSATION FLOW ANALYSIS ===")
            
            if len(messages) <= 4:
                context_lines.append("Conversation Status: NEW CONVERSATION")
                context_lines.append("Recommendation: Use appropriate greetings and introductions")
            elif len(messages) <= 10:
                context_lines.append("Conversation Status: EARLY STAGE")
                context_lines.append("Recommendation: Use friendly tone, avoid repetitive greetings")
            else:
                context_lines.append("Conversation Status: ONGOING CONVERSATION")
                context_lines.append("Recommendation: Use natural conversation continuations (Claro, Perfecto, Excelente, etc.)")
                context_lines.append("IMPORTANT: DO NOT use generic greetings like '¡Hola Steve! 😊'")
            
            # Conversation duration
            if len(messages) >= 2:
                first_msg = messages[0]
                last_msg = messages[-1]
                
                first_time = first_msg.get('timestamp')
                last_time = last_msg.get('timestamp')
                
                if first_time and last_time:
                    if isinstance(first_time, str):
                        first_time = datetime.fromisoformat(first_time.replace('Z', '+00:00'))
                    if isinstance(last_time, str):
                        last_time = datetime.fromisoformat(last_time.replace('Z', '+00:00'))
                    
                    duration = last_time - first_time
                    context_lines.append(f"- Duration: {duration}")
                    
                    # Add conversation age context
                    if duration.total_seconds() > 3600:  # More than 1 hour
                        context_lines.append("- Conversation Age: LONG-RUNNING (over 1 hour)")
                        context_lines.append("- Tone: Use natural continuations, avoid greetings")
                    elif duration.total_seconds() > 300:  # More than 5 minutes
                        context_lines.append("- Conversation Age: ONGOING (over 5 minutes)")
                        context_lines.append("- Tone: Use natural continuations, avoid greetings")
                    else:
                        context_lines.append("- Conversation Age: RECENT (under 5 minutes)")
                        context_lines.append("- Tone: Can use friendly tone, avoid repetitive greetings")
            
            # Find the last customer message for easy identification
            last_customer_message = None
            for msg in reversed(messages):
                if msg.get('direction') == 'inbound':
                    last_customer_message = msg.get('text_content', msg.get('text', msg.get('content', '')))
                    break
            
            if last_customer_message:
                context_lines.append("")
                context_lines.append("=== LAST CUSTOMER MESSAGE ===")
                context_lines.append(f"Customer: {last_customer_message}")
                context_lines.append("")
                context_lines.append("IMPORTANT: This is the message you need to respond to!")
                
                # Add response style recommendation based on conversation flow
                if len(messages) > 10:
                    context_lines.append("RESPONSE STYLE: Use enthusiastic conversation continuations like:")
                    context_lines.append("- '¡Claro Steve! 🛜 Ofrecemos...'")
                    context_lines.append("- '¡Perfecto! 🚀 Aquí tienes toda la información sobre...'")
                    context_lines.append("- '¡Excelente pregunta! 💫 Nuestras velocidades incluyen...'")
                    context_lines.append("- '¡Por supuesto! ⚡ Contamos con...'")
                    context_lines.append("AVOID: Generic greetings like '¡Hola Steve! 😊'")
                    context_lines.append("REMEMBER: Show enthusiasm about ADN's services! 🎉")
                else:
                    context_lines.append("RESPONSE STYLE: Can use enthusiastic tone, but avoid repetitive greetings")
                    context_lines.append("REMEMBER: Show excitement about helping customers! 🚀")
            
            result = "\n".join(context_lines)
            
            logger.info(f"Retrieved conversation context for {conversation_id}: {len(messages)} messages")
            
            return result
            
        except Exception as e:
            error_msg = f"Error retrieving conversation context: {str(e)}"
            logger.error(error_msg)
            return error_msg


def create_conversation_context_tool() -> StructuredTool:
    """Create a structured conversation context tool for use in LangGraph."""
    
    tool = ConversationContextTool()
    
    return StructuredTool(
        name=tool.name,
        description=tool.description,
        func=tool._run,
        coroutine=tool._arun,
        args_schema=ConversationContextInput
    )
