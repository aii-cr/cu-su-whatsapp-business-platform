"""
Conversation memory service for AI agent.
Handles conversation history, session management, and context persistence.
"""

import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict

from langchain.memory import ConversationBufferMemory
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from app.core.logger import logger
from app.services.ai.config import ai_config


class ConversationMemoryService:
    """
    Service for managing conversation memory and context across sessions.
    """
    
    def __init__(self):
        """Initialize the memory service."""
        self.conversation_memories: Dict[str, ConversationBufferMemory] = {}
        self.session_data: Dict[str, Dict[str, Any]] = defaultdict(dict)
        self.last_activity: Dict[str, datetime] = {}
        self._cleanup_task: Optional[asyncio.Task] = None
        
    def _start_cleanup_task(self):
        """Start the cleanup task if not already running."""
        if self._cleanup_task is None or self._cleanup_task.done():
            try:
                self._cleanup_task = asyncio.create_task(self._cleanup_expired_sessions())
            except RuntimeError:
                # No running event loop, will start when service is used
                pass
    
    async def get_conversation_memory(self, conversation_id: str) -> ConversationBufferMemory:
        """
        Get or create conversation memory for a specific conversation.
        
        Args:
            conversation_id: Conversation identifier
            
        Returns:
            Conversation memory instance
        """
        # Start cleanup task if not running
        self._start_cleanup_task()
        
        if conversation_id not in self.conversation_memories:
            self.conversation_memories[conversation_id] = ConversationBufferMemory(
                memory_key="conversation_history",
                return_messages=True,
                max_token_limit=ai_config.max_context_tokens
            )
            logger.info(f"Created new conversation memory for {conversation_id}")
        
        # Update last activity
        self.last_activity[conversation_id] = datetime.now()
        
        return self.conversation_memories[conversation_id]
    
    def get_session_data(self, conversation_id: str) -> Dict[str, Any]:
        """
        Get session data for a conversation.
        
        Args:
            conversation_id: Conversation identifier
            
        Returns:
            Session data dictionary
        """
        return self.session_data[conversation_id]
    
    def update_session_data(self, conversation_id: str, data: Dict[str, Any]):
        """
        Update session data for a conversation.
        
        Args:
            conversation_id: Conversation identifier
            data: Data to update
        """
        self.session_data[conversation_id].update(data)
        self.last_activity[conversation_id] = datetime.now()
    
    async def load_conversation_history(self, conversation_id: str) -> List[Dict[str, Any]]:
        """
        Load conversation history from database.
        
        Args:
            conversation_id: Conversation identifier
            
        Returns:
            List of previous messages
        """
        try:
            # Import here to avoid circular imports
            from app.services import message_service
            
            # Get recent messages for this conversation
            result = await message_service.get_conversation_messages(
                conversation_id=conversation_id,
                limit=10,  # Last 10 messages for context
                offset=0,
                sort_by="timestamp",
                sort_order="desc"  # Get most recent first
            )
            
            # Get messages from result
            messages = result.get("messages", [])
            
            # Format messages for memory
            history = []
            for msg in messages:
                if msg.get("direction") == "inbound":
                    history.append({
                        "role": "user",
                        "content": msg.get("text_content", ""),
                        "timestamp": msg.get("timestamp"),
                        "message_id": str(msg.get("_id"))
                    })
                elif msg.get("direction") == "outbound" and msg.get("sender_role") == "ai_assistant":
                    history.append({
                        "role": "assistant", 
                        "content": msg.get("text_content", ""),
                        "timestamp": msg.get("timestamp"),
                        "message_id": str(msg.get("_id"))
                    })
            
            # Reverse to get chronological order
            history.reverse()
            
            return history
            
        except Exception as e:
            logger.error(f"Error loading conversation history: {str(e)}")
            return []
    
    def create_conversation_summary(self, history: List[Dict[str, Any]]) -> str:
        """
        Create a summary of conversation history for context.
        
        Args:
            history: Conversation history
            
        Returns:
            Compressed summary
        """
        if not history:
            return ""
        
        try:
            # Create a simple summary of key points
            user_messages = [msg["content"] for msg in history if msg["role"] == "user"]
            ai_messages = [msg["content"] for msg in history if msg["role"] == "assistant"]
            
            summary_parts = []
            
            if user_messages:
                # Extract key topics from user messages
                topics = []
                for msg in user_messages[-3:]:  # Last 3 user messages
                    if "reserva" in msg.lower() or "booking" in msg.lower():
                        topics.append("booking")
                    elif "pago" in msg.lower() or "payment" in msg.lower():
                        topics.append("payment")
                    elif "precio" in msg.lower() or "price" in msg.lower():
                        topics.append("pricing")
                    elif "horario" in msg.lower() or "schedule" in msg.lower():
                        topics.append("scheduling")
                
                if topics:
                    summary_parts.append(f"Topics discussed: {', '.join(set(topics))}")
            
            if ai_messages:
                # Check if AI provided specific information
                last_ai_msg = ai_messages[-1] if ai_messages else ""
                if "precio" in last_ai_msg.lower() or "price" in last_ai_msg.lower():
                    summary_parts.append("Pricing information provided")
                if "reserva" in last_ai_msg.lower() or "booking" in last_ai_msg.lower():
                    summary_parts.append("Booking process discussed")
            
            return "; ".join(summary_parts) if summary_parts else "General conversation"
            
        except Exception as e:
            logger.error(f"Error creating conversation summary: {str(e)}")
            return ""
    
    async def add_interaction_to_memory(
        self, 
        conversation_id: str, 
        user_message: str, 
        ai_response: str
    ):
        """
        Add an interaction to conversation memory.
        
        Args:
            conversation_id: Conversation identifier
            user_message: User's message
            ai_response: AI's response
        """
        try:
            memory = await self.get_conversation_memory(conversation_id)
            
            # Add the interaction to memory
            memory.chat_memory.add_user_message(user_message)
            memory.chat_memory.add_ai_message(ai_response)
            
            logger.debug(f"Updated conversation memory for {conversation_id}")
            
        except Exception as e:
            logger.error(f"Error updating conversation memory: {str(e)}")
    
    async def get_conversation_context(self, conversation_id: str) -> Dict[str, Any]:
        """
        Get comprehensive conversation context.
        
        Args:
            conversation_id: Conversation identifier
            
        Returns:
            Context dictionary with history, summary, and session data
        """
        try:
            memory = await self.get_conversation_memory(conversation_id)
            session_data = self.get_session_data(conversation_id)
            
            # Get memory messages
            memory_messages = memory.chat_memory.messages if memory.chat_memory.messages else []
            
            # Convert to our format
            history = []
            for msg in memory_messages:
                if isinstance(msg, HumanMessage):
                    history.append({
                        "role": "user",
                        "content": msg.content,
                        "timestamp": datetime.now().isoformat(),
                        "message_id": f"memory_{len(history)}"
                    })
                elif isinstance(msg, AIMessage):
                    history.append({
                        "role": "assistant",
                        "content": msg.content,
                        "timestamp": datetime.now().isoformat(),
                        "message_id": f"memory_{len(history)}"
                    })
            
            summary = self.create_conversation_summary(history)
            
            # Format last_activity for JSON serialization
            last_activity = self.last_activity.get(conversation_id)
            if last_activity:
                last_activity = last_activity.isoformat()
            
            return {
                "conversation_id": conversation_id,
                "history": history,
                "summary": summary,
                "session_data": session_data,
                "last_activity": last_activity,
                "memory_size": len(memory_messages)
            }
        except Exception as e:
            logger.error(f"Error getting conversation context for {conversation_id}: {str(e)}")
            # Return a default context structure
            return {
                "conversation_id": conversation_id,
                "history": [],
                "summary": "",
                "session_data": {},
                "last_activity": None,
                "memory_size": 0
            }
    
    async def clear_conversation_memory(self, conversation_id: str):
        """
        Clear conversation memory and session data.
        
        Args:
            conversation_id: Conversation identifier
        """
        if conversation_id in self.conversation_memories:
            del self.conversation_memories[conversation_id]
        
        if conversation_id in self.session_data:
            del self.session_data[conversation_id]
        
        if conversation_id in self.last_activity:
            del self.last_activity[conversation_id]
        
        logger.info(f"Cleared conversation memory for {conversation_id}")
    
    async def _cleanup_expired_sessions(self):
        """Clean up expired conversation sessions."""
        while True:
            try:
                current_time = datetime.now()
                expired_conversations = []
                
                for conversation_id, last_activity in self.last_activity.items():
                    # Expire sessions after 24 hours of inactivity
                    if current_time - last_activity > timedelta(hours=24):
                        expired_conversations.append(conversation_id)
                
                for conversation_id in expired_conversations:
                    self.clear_conversation_memory(conversation_id)
                    logger.info(f"Cleaned up expired session for {conversation_id}")
                
                # Run cleanup every hour
                await asyncio.sleep(3600)
                
            except Exception as e:
                logger.error(f"Error in session cleanup: {str(e)}")
                await asyncio.sleep(3600)  # Continue despite errors
    
    async def get_memory_stats(self) -> Dict[str, Any]:
        """
        Get memory service statistics.
        
        Returns:
            Statistics dictionary
        """
        return {
            "active_conversations": len(self.conversation_memories),
            "total_sessions": len(self.session_data),
            "memory_usage": {
                conversation_id: len(memory.chat_memory.messages) if memory.chat_memory.messages else 0
                for conversation_id, memory in self.conversation_memories.items()
            },
            "last_activity": {
                conversation_id: last_activity.isoformat()
                for conversation_id, last_activity in self.last_activity.items()
            }
        }


# Global memory service instance
memory_service = ConversationMemoryService()
