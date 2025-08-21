"""
Main AI agent service for WhatsApp Business chatbot.
Handles message processing, database integration, and response generation.
"""

import asyncio
import re
from typing import Dict, Any, Optional
from datetime import datetime, timezone

from app.core.logger import logger
from app.services.ai.config import ai_config
from app.services.ai.graphs.whatsapp_agent import WhatsAppAgent, AgentState
from app.services.ai.rag.ingest import ingest_documents, check_collection_health
from app.services.ai.memory_service import memory_service
from app.services import message_service, conversation_service
from app.services.websocket.websocket_service import manager, WebSocketService


def strip_markdown(text: str) -> str:
    """
    Strip markdown formatting from text to make it suitable for WhatsApp.
    
    Args:
        text: Text with markdown formatting
        
    Returns:
        Clean text without markdown
    """
    if not text:
        return text
    
    # Remove markdown headers
    text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)
    
    # Remove bold/italic markers
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)  # **bold**
    text = re.sub(r'\*(.*?)\*', r'\1', text)      # *italic*
    text = re.sub(r'__(.*?)__', r'\1', text)      # __bold__
    text = re.sub(r'_(.*?)_', r'\1', text)        # _italic_
    
    # Remove code blocks
    text = re.sub(r'```.*?```', '', text, flags=re.DOTALL)
    text = re.sub(r'`(.*?)`', r'\1', text)        # inline code
    
    # Remove links but keep text
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
    
    # Remove strikethrough
    text = re.sub(r'~~(.*?)~~', r'\1', text)
    
    # Convert bullet points to WhatsApp-style
    text = re.sub(r'^\s*[-*+]\s+', '• ', text, flags=re.MULTILINE)
    
    # Remove blockquotes
    text = re.sub(r'^\s*>\s+', '', text, flags=re.MULTILINE)
    
    # Clean up extra whitespace
    text = re.sub(r'\n\s*\n', '\n\n', text)  # Multiple newlines to double newlines
    text = re.sub(r'[ \t]+', ' ', text)      # Multiple spaces to single space
    
    # Trim whitespace
    text = text.strip()
    
    return text


class AgentService:
    """
    Main AI agent service that coordinates all chatbot functionality.
    """
    
    def __init__(self):
        """Initialize the agent service."""
        self.agent = WhatsAppAgent()
        self._initialized = False
        
    async def initialize(self):
        """Initialize the agent service and ensure knowledge base is ready."""
        if self._initialized:
            return
        
        logger.info("Initializing AI agent service...")
        
        try:
            # Check collection health
            health = await check_collection_health()
            
            if not health.get("collection_exists", False) or health.get("vectors_count", 0) == 0:
                logger.info("Knowledge base empty, running initial ingestion...")
                
                ingestion_result = await ingest_documents()
                
                if ingestion_result.success:
                    logger.info(
                        f"Successfully ingested {ingestion_result.chunks_stored} chunks "
                        f"from {ingestion_result.documents_processed} documents"
                    )
                else:
                    logger.error(f"Failed to ingest documents: {ingestion_result.errors}")
                    
            self._initialized = True
            logger.info("AI agent service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize AI agent service: {str(e)}")
            raise
    
    async def process_whatsapp_message(
        self,
        conversation_id: str,
        message_id: str,
        user_text: str,
        customer_phone: str,
        ai_autoreply_enabled: bool = True,
        is_first_message: bool = False
    ) -> Dict[str, Any]:
        """
        Process a WhatsApp message and generate AI response.
        
        Args:
            conversation_id: Conversation identifier
            message_id: Message identifier
            user_text: Customer message text
            customer_phone: Customer phone number
            ai_autoreply_enabled: Whether auto-reply is enabled
            is_first_message: Whether this is the first message
            
        Returns:
            Processing result with response and metadata
        """
        await self.initialize()
        
        logger.info(
            f"Processing WhatsApp message (conversation: {conversation_id}, "
            f"autoreply: {ai_autoreply_enabled}): '{user_text[:100]}...'"
        )
        
        try:
            # Process message through agent
            agent_result = await self.agent.process_message(
                user_text=user_text,
                conversation_id=conversation_id,
                customer_phone=customer_phone,
                message_id=message_id,
                ai_autoreply_enabled=ai_autoreply_enabled,
                is_first_message=is_first_message
            )
            
            # Handle the response
            if agent_result.get("reply") == "NO_REPLY":
                logger.info(f"No AI reply generated for conversation {conversation_id} (auto-reply disabled)")
                return {
                    "success": True,
                    "ai_response_sent": False,
                    "reason": "auto_reply_disabled"
                }
            
            # Strip markdown from AI response for WhatsApp
            raw_response = agent_result["reply"]
            clean_response = strip_markdown(raw_response)
            
            logger.info(f"🤖 [AI] Original response: {raw_response[:100]}...")
            logger.info(f"🤖 [AI] Cleaned response: {clean_response[:100]}...")
            
            # Send AI response via WhatsApp and store as message
            ai_message_id = await self._send_and_store_ai_response(
                conversation_id=conversation_id,
                response_text=clean_response,
                confidence=agent_result.get("confidence", 0.0),
                metadata=agent_result,
                customer_phone=customer_phone
            )
            
            # Send real-time notification via WebSocket
            try:
                # Use service singletons from the centralized services module
                from app.services import websocket_service

                # Get the full message data for WebSocket notification
                ai_message = await message_service.get_message(ai_message_id)
                if ai_message:
                    await websocket_service.notify_ai_response(
                        conversation_id=conversation_id,
                        message_data=ai_message
                    )
                    logger.info(f"🤖 [WS] Sent AI response notification for conversation {conversation_id}")
            except Exception as ws_error:
                logger.warning(f"⚠️ [WS] Failed to send AI response notification: {str(ws_error)}")
                # Don't fail the entire flow if WebSocket notification fails
            
            # Update conversation metadata
            await self._update_conversation_metadata(
                conversation_id=conversation_id,
                agent_result=agent_result
            )
            
            return {
                "success": True,
                "ai_response_sent": True,
                "ai_message_id": ai_message_id,
                "response_text": clean_response,
                "confidence": agent_result.get("confidence", 0.0),
                "requires_human_handoff": agent_result.get("requires_human_handoff", False),
                "processing_time_ms": self._calculate_processing_time(agent_result),
                "node_history": agent_result.get("node_history", [])
            }
            
        except Exception as e:
            logger.error(f"Error processing WhatsApp message: {str(e)}")
            
            # Send fallback response
            fallback_message = "Lo siento, ocurrió un error procesando tu mensaje. Un agente te contactará pronto."
            
            ai_message_id = await self._send_and_store_ai_response(
                conversation_id=conversation_id,
                response_text=fallback_message,
                confidence=0.0,
                metadata={"error": str(e), "fallback": True},
                customer_phone=customer_phone
            )
            
            # Send real-time notification for fallback response
            try:
                from app.services import websocket_service

                # Get the full message data for WebSocket notification
                ai_message = await message_service.get_message(ai_message_id)
                if ai_message:
                    await websocket_service.notify_ai_response(
                        conversation_id=conversation_id,
                        message_data=ai_message
                    )
                    logger.info(f"🤖 [WS] Sent fallback AI response notification for conversation {conversation_id}")
            except Exception as ws_error:
                logger.warning(f"⚠️ [WS] Failed to send fallback AI response notification: {str(ws_error)}")
                # Don't fail the entire flow if WebSocket notification fails
            
            return {
                "success": False,
                "ai_response_sent": True,
                "ai_message_id": ai_message_id,
                "response_text": fallback_message,
                "error": str(e),
                "requires_human_handoff": True
            }
    
    async def _send_and_store_ai_response(
        self,
        conversation_id: str,
        response_text: str,
        confidence: float,
        metadata: Dict[str, Any],
        customer_phone: str
    ) -> str:
        """
        Send AI response via WhatsApp API and store as a message in the database.
        
        Args:
            conversation_id: Conversation identifier
            response_text: AI-generated response text
            confidence: Response confidence score
            metadata: Additional metadata from agent processing
            customer_phone: Customer phone number
            
        Returns:
            Message ID of the stored response
        """
        try:
            # Send message via WhatsApp API
            from app.services import whatsapp_service
            
            whatsapp_response = await whatsapp_service.send_text_message(
                to_number=customer_phone,
                text=response_text
            )
            
            whatsapp_message_id = None
            if whatsapp_response and whatsapp_response.get("messages"):
                whatsapp_message_id = whatsapp_response["messages"][0].get("id")
            
            # Store message using the correct API (without metadata parameter)
            message = await message_service.create_message(
                conversation_id=conversation_id,
                message_type="text",
                direction="outbound", 
                sender_role="ai_assistant",
                text_content=response_text,
                whatsapp_message_id=whatsapp_message_id,
                whatsapp_data=whatsapp_response,
                status="sent"
            )
            message_id = message["_id"]
            
            logger.info(
                f"Stored AI response message {message_id} for conversation {conversation_id} "
                f"(confidence: {confidence:.2f})"
            )
            
            return str(message_id)
            
        except Exception as e:
            logger.error(f"Error storing AI response: {str(e)}")
            raise
    

    
    async def _update_conversation_metadata(
        self,
        conversation_id: str,
        agent_result: AgentState
    ):
        """
        Update conversation metadata with AI interaction info.
        
        Args:
            conversation_id: Conversation identifier
            agent_result: Agent processing result
        """
        try:
            metadata_update = {
                "ai_last_interaction": datetime.now(timezone.utc).isoformat(),
                "ai_confidence_score": agent_result.get("confidence", 0.0),
                "ai_language_detected": agent_result.get("customer_language", "es"),
                "ai_requires_handoff": agent_result.get("requires_human_handoff", False)
            }
            
            await conversation_service.update_conversation(
                conversation_id=conversation_id,
                update_data=metadata_update,
                updated_by=None  # System update
            )
            
        except Exception as e:
            logger.error(f"Error updating conversation metadata: {str(e)}")
            # Don't raise - metadata update failure shouldn't break the flow
    
    def _calculate_processing_time(self, agent_result: AgentState) -> int:
        """Calculate total processing time in milliseconds."""
        try:
            start_time = datetime.fromisoformat(agent_result["processing_start_time"])
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            return int(processing_time)
        except:
            return 0
    
    async def health_check(self) -> Dict[str, Any]:
        """Comprehensive health check for the agent service."""
        try:
            # Check agent health
            agent_health = await self.agent.health_check()
            
            # Check collection health
            collection_health = await check_collection_health()
            
            # Get memory service statistics
            memory_stats = memory_service.get_memory_stats()
            
            return {
                "status": "healthy" if agent_health["status"] == "healthy" else "unhealthy",
                "agent": agent_health,
                "knowledge_base": collection_health,
                "memory_service": memory_stats,
                "initialized": self._initialized,
                "config": {
                    "model": ai_config.openai_model,
                    "confidence_threshold": ai_config.confidence_threshold,
                    "max_response_length": ai_config.max_response_length
                },
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Agent service health check failed: {str(e)}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def get_conversation_context(self, conversation_id: str) -> Dict[str, Any]:
        """
        Get conversation context and memory information.
        
        Args:
            conversation_id: Conversation identifier
            
        Returns:
            Conversation context information
        """
        try:
            return memory_service.get_conversation_context(conversation_id)
        except Exception as e:
            logger.error(f"Error getting conversation context: {str(e)}")
            return {"error": str(e)}
    
    async def clear_conversation_memory(self, conversation_id: str) -> Dict[str, Any]:
        """
        Clear conversation memory and session data.
        
        Args:
            conversation_id: Conversation identifier
            
        Returns:
            Result of the clear operation
        """
        try:
            memory_service.clear_conversation_memory(conversation_id)
            
            logger.info(f"Cleared conversation memory for {conversation_id}")
            
            return {
                "success": True,
                "conversation_id": conversation_id,
                "message": "Conversation memory cleared successfully"
            }
            
        except Exception as e:
            logger.error(f"Error clearing conversation memory: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_memory_statistics(self) -> Dict[str, Any]:
        """
        Get memory service statistics.
        
        Returns:
            Memory statistics
        """
        try:
            return memory_service.get_memory_stats()
        except Exception as e:
            logger.error(f"Error getting memory statistics: {str(e)}")
            return {"error": str(e)}
    
    async def toggle_autoreply(
        self,
        conversation_id: str,
        enabled: bool,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Toggle auto-reply for a conversation.
        
        Args:
            conversation_id: Conversation identifier
            enabled: Whether to enable auto-reply
            user_id: User who made the change (for audit)
            
        Returns:
            Result of the toggle operation
        """
        try:
            # Update conversation metadata
            await conversation_service.update_conversation_metadata(
                conversation_id=conversation_id,
                metadata={"ai_autoreply_enabled": enabled}
            )
            
            logger.info(
                f"Auto-reply {'enabled' if enabled else 'disabled'} for conversation {conversation_id} "
                f"by user {user_id}"
            )
            
            # Send notification about the change
            await WebSocketService.notify_autoreply_toggled(
                conversation_id=conversation_id,
                enabled=enabled,
                changed_by=user_id
            )
            
            return {
                "success": True,
                "conversation_id": conversation_id,
                "ai_autoreply_enabled": enabled
            }
            
        except Exception as e:
            logger.error(f"Error toggling auto-reply: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }


# Global agent service instance
agent_service = AgentService()
