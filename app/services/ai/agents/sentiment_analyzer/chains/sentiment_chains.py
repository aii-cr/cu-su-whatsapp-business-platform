"""
LangChain chains for sentiment analysis.
Uses structured output to analyze message sentiment and return appropriate emoji.
"""

import asyncio
import time
from typing import Dict, Any, Optional, List
from pathlib import Path

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field

from app.core.logger import logger
from app.services.ai.config import ai_config
from app.services.ai.agents.sentiment_analyzer.config import sentiment_config
from app.services.ai.agents.sentiment_analyzer.schemas import (
    SentimentType, SentimentEmoji, SentimentAnalysisResponse
)


class SentimentAnalysisSchema(BaseModel):
    """Structured output schema for sentiment analysis."""
    sentiment_emoji: SentimentEmoji = Field(..., description="The most appropriate emoji from the list")


class SentimentChains:
    """
    LangChain chains for sentiment analysis.
    """
    
    def __init__(self, llm: Optional[ChatOpenAI] = None):
        """
        Initialize sentiment analysis chains.
        
        Args:
            llm: Language model to use for sentiment analysis
        """
        self._llm = llm
        self._chains_initialized = False
        self._parser = PydanticOutputParser(pydantic_object=SentimentAnalysisSchema)
        
    def _get_llm(self) -> ChatOpenAI:
        """Get or create the language model."""
        if self._llm is None:
            self._llm = ChatOpenAI(
                api_key=ai_config.openai_api_key,
                model=sentiment_config.model_name,
                temperature=sentiment_config.temperature,
                max_tokens=sentiment_config.max_tokens
            )
        return self._llm
    
    def _setup_chains(self):
        """Initialize the sentiment analysis chain."""
        if self._chains_initialized:
            return
            
        self._llm = self._get_llm()
        
        # Load sentiment analysis prompt
        prompt_template = self._load_sentiment_prompt()
        
        # Create the chain (no structured output for simple emoji response)
        self._sentiment_chain = prompt_template | self._llm
        
        self._chains_initialized = True
        logger.info("Sentiment analysis chains initialized")
    
    def _load_sentiment_prompt(self) -> ChatPromptTemplate:
        """Load the sentiment analysis prompt template."""
        try:
            # Try to load from file first
            prompt_path = Path("app/services/ai/agents/sentiment_analyzer/prompts/sentiment_analysis.md")
            if prompt_path.exists():
                prompt_content = prompt_path.read_text(encoding="utf-8")
                return ChatPromptTemplate.from_template(prompt_content)
        except Exception as e:
            logger.warning(f"Could not load sentiment prompt from file: {str(e)}")
        
        # Fallback to inline prompt
        fallback_prompt = """
        You are a sentiment analysis expert. Your task is to analyze the customer's emotional state based on ALL their messages in the conversation and respond with ONLY the most appropriate emoji.
        
        ## Available Emojis
        {sentiment_emojis}
        
        ## Customer Messages Context
        {customer_messages_context}
        
        ## Instructions
        1. Analyze the customer's emotional state across ALL their messages
        2. Consider the progression of their mood throughout the conversation
        3. Respond with ONLY the emoji that best represents their current emotional state
        4. Do not provide any explanation, reasoning, or additional text
        5. Respond with exactly one emoji from the provided list
        
        ## Response
        Respond with ONLY the emoji:
        """
        
        return ChatPromptTemplate.from_template(fallback_prompt)
    
    async def analyze_sentiment(
        self, 
        conversation_id: str,
        customer_messages: List[Dict[str, Any]]
    ) -> SentimentAnalysisResponse:
        """
        Analyze sentiment based on all customer messages in the conversation.
        
        Args:
            conversation_id: Conversation ID
            customer_messages: List of all customer messages in the conversation
            
        Returns:
            SentimentAnalysisResponse with analysis results
        """
        start_time = time.time()
        
        try:
            # Setup chains if not initialized
            if not self._chains_initialized:
                self._setup_chains()
            
            # Format customer messages context
            customer_messages_context = self._format_customer_messages(customer_messages)
            
            # Prepare prompt variables
            prompt_vars = {
                "customer_messages_context": customer_messages_context,
                "sentiment_emojis": sentiment_config.sentiment_emojis
            }
            
            # Run sentiment analysis with timeout
            try:
                result = await asyncio.wait_for(
                    self._sentiment_chain.ainvoke(prompt_vars),
                    timeout=sentiment_config.timeout_seconds
                )
            except asyncio.TimeoutError:
                logger.error(f"Sentiment analysis timed out after {sentiment_config.timeout_seconds} seconds")
                raise Exception("Sentiment analysis timed out")
            
            # Calculate processing time
            processing_time_ms = (time.time() - start_time) * 1000
            
            # Extract emoji from response
            response_text = result.content.strip()
            logger.info(f"Raw sentiment response: {response_text}")
            
            # Find the emoji in the response
            sentiment_emoji = self._extract_emoji_from_response(response_text)
            
            # Create response with default values for removed fields
            response = SentimentAnalysisResponse(
                conversation_id=conversation_id,
                message_id="",  # Will be set by caller
                sentiment_type="neutral",  # Default since we removed it from schema
                sentiment_emoji=sentiment_emoji,
                confidence=0.8,  # Default confidence since we removed it from schema
                reasoning="Analysis based on all customer messages",  # Default reasoning
                language="auto",  # Default language since we removed it from schema
                processing_time_ms=processing_time_ms
            )
            
            logger.info(f"Sentiment analysis completed: {sentiment_emoji}")
            return response
            
        except Exception as e:
            logger.error(f"Error in sentiment analysis: {str(e)}")
            logger.error(f"Error details: {type(e).__name__}: {str(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise
    
    def _format_customer_messages(self, customer_messages: List[Dict[str, Any]]) -> str:
        """
        Format customer messages for the prompt context.
        
        Args:
            customer_messages: List of customer message dictionaries
            
        Returns:
            Formatted string with all customer messages
        """
        if not customer_messages:
            return "No customer messages available."
        
        formatted_messages = []
        for i, msg in enumerate(customer_messages, 1):
            content = msg.get("text_content", "") or msg.get("content", "")
            timestamp = msg.get("timestamp", msg.get("created_at", ""))
            
            # Format timestamp if available
            if timestamp:
                if isinstance(timestamp, str):
                    time_str = timestamp
                else:
                    time_str = timestamp.strftime("%Y-%m-%d %H:%M:%S")
            else:
                time_str = "Unknown time"
            
            formatted_messages.append(f"Message {i} ({time_str}): {content}")
        
        return "\n".join(formatted_messages)
    
    def _extract_emoji_from_response(self, response_text: str) -> str:
        """
        Extract emoji from LLM response.
        
        Args:
            response_text: Raw response from LLM
            
        Returns:
            Extracted emoji or default emoji
        """
        # Available emojis
        available_emojis = sentiment_config.sentiment_emojis
        
        # Look for any of the available emojis in the response
        for emoji in available_emojis:
            if emoji in response_text:
                logger.info(f"Found emoji in response: {emoji}")
                return emoji
        
        # If no emoji found, try to extract any emoji
        import re
        emoji_pattern = re.compile(r'[😊😐😞😤😡🤔😌😰😍😔]')
        emoji_match = emoji_pattern.search(response_text)
        
        if emoji_match:
            found_emoji = emoji_match.group()
            logger.info(f"Found emoji using regex: {found_emoji}")
            return found_emoji
        
        # Default fallback
        logger.warning(f"No emoji found in response: {response_text}")
        return "😐"  # Default neutral emoji
    
    async def analyze_sentiment_batch(
        self, 
        conversations_messages: List[Dict[str, Any]]
    ) -> List[SentimentAnalysisResponse]:
        """
        Analyze sentiment for multiple conversations in batch.
        
        Args:
            conversations_messages: List of conversation data with customer messages
            
        Returns:
            List of SentimentAnalysisResponse objects
        """
        if not conversations_messages:
            return []
        
        # Setup chains if not initialized
        if not self._chains_initialized:
            self._setup_chains()
        
        results = []
        
        # Process in batches
        batch_size = sentiment_config.batch_size
        for i in range(0, len(conversations_messages), batch_size):
            batch = conversations_messages[i:i + batch_size]
            
            # Process batch concurrently
            batch_tasks = []
            for conv_data in batch:
                task = self.analyze_sentiment(
                    conversation_id=conv_data["conversation_id"],
                    customer_messages=conv_data["customer_messages"]
                )
                batch_tasks.append(task)
            
            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
            
            # Handle results
            for j, result in enumerate(batch_results):
                if isinstance(result, Exception):
                    logger.error(f"Error analyzing conversation {i + j}: {str(result)}")
                    continue
                
                results.append(result)
        
        return results
