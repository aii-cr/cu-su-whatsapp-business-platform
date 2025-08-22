"""
LangChain chains for conversation summarization.
"""

import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
from operator import itemgetter

from langchain_core.language_models import BaseLanguageModel
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_openai import ChatOpenAI

from app.core.logger import logger
from app.services.ai.config import ai_config
from app.core.config import settings
from app.services.ai.agents.conversation_summarizer.prompts.summarization_prompts import (
    get_summary_prompt,
    get_key_points_prompt,
    get_sentiment_prompt,
    get_topics_prompt
)
from app.services.ai.agents.conversation_summarizer.schemas import (
    ConversationData,
    SummarizationConfig,
    SummarizationResult,
    ConversationSummaryResponse
)


class SummarizationChains:
    """
    LangChain chains for conversation summarization.
    """
    
    def __init__(self, llm: Optional[BaseLanguageModel] = None):
        """
        Initialize summarization chains.
        
        Args:
            llm: Language model to use for summarization
        """
        self._llm = llm
        self._chains_initialized = False
        self._chains = {}
    
    def _get_llm(self) -> BaseLanguageModel:
        """Get or create the language model."""
        if self._llm is None:
            self._llm = ChatOpenAI(
                api_key=settings.OPENAI_API_KEY,
                model=settings.OPENAI_MODEL,
                temperature=0.3,
                max_tokens=2000
            )
        return self._llm
    
    def _setup_chains(self):
        """Setup all summarization chains."""
        if self._chains_initialized:
            return
            
        llm = self._get_llm()
        
        # Main summarization chain with updated prompt
        self._chains['summary'] = (
            {
                "conversation_text": itemgetter("conversation_text"),
                "summary_style": itemgetter("summary_style"),
                "max_length": itemgetter("max_length"),
                "human_agents": itemgetter("human_agents"),
                "ai_message_count": itemgetter("ai_message_count")
            }
            | get_summary_prompt()
            | llm
            | StrOutputParser()
        )
        
        # Key points extraction chain with updated prompt
        self._chains['key_points'] = (
            {
                "conversation_text": itemgetter("conversation_text"),
                "ai_message_count": itemgetter("ai_message_count")
            }
            | get_key_points_prompt()
            | llm
            | StrOutputParser()
        )
        
        # Sentiment analysis chain
        self._chains['sentiment'] = (
            {"conversation_text": itemgetter("conversation_text")}
            | get_sentiment_prompt()
            | llm
            | StrOutputParser()
        )
        
        # Topic extraction chain
        self._chains['topics'] = (
            {"conversation_text": itemgetter("conversation_text")}
            | get_topics_prompt()
            | llm
            | StrOutputParser()
        )
        
        # Combined analysis chain - create individual chains first
        summary_chain = (
            {
                "conversation_text": itemgetter("conversation_text"),
                "summary_style": itemgetter("summary_style"),
                "max_length": itemgetter("max_length"),
                "human_agents": itemgetter("human_agents"),
                "ai_message_count": itemgetter("ai_message_count")
            }
            | get_summary_prompt()
            | llm
            | StrOutputParser()
        )
        
        key_points_chain = (
            {
                "conversation_text": itemgetter("conversation_text"),
                "ai_message_count": itemgetter("ai_message_count")
            }
            | get_key_points_prompt()
            | llm
            | StrOutputParser()
        )
        
        sentiment_chain = (
            {"conversation_text": itemgetter("conversation_text")}
            | get_sentiment_prompt()
            | llm
            | StrOutputParser()
        )
        
        topics_chain = (
            {"conversation_text": itemgetter("conversation_text")}
            | get_topics_prompt()
            | llm
            | StrOutputParser()
        )
        
        # Now create the combined chain
        self._chains['combined'] = (
            {
                "conversation_text": itemgetter("conversation_text"),
                "summary_style": itemgetter("summary_style"),
                "max_length": itemgetter("max_length"),
                "human_agents": itemgetter("human_agents"),
                "ai_message_count": itemgetter("ai_message_count")
            }
            | {
                "summary": summary_chain,
                "key_points": key_points_chain,
                "sentiment": sentiment_chain,
                "topics": topics_chain
            }
        )
        
        self._chains_initialized = True
    
    @property
    def summary_chain(self):
        """Get the summary chain, initializing if needed."""
        if not self._chains_initialized:
            self._setup_chains()
        return self._chains['summary']
    
    @property
    def key_points_chain(self):
        """Get the key points chain, initializing if needed."""
        if not self._chains_initialized:
            self._setup_chains()
        return self._chains['key_points']
    
    @property
    def sentiment_chain(self):
        """Get the sentiment chain, initializing if needed."""
        if not self._chains_initialized:
            self._setup_chains()
        return self._chains['sentiment']
    
    @property
    def topics_chain(self):
        """Get the topics chain, initializing if needed."""
        if not self._chains_initialized:
            self._setup_chains()
        return self._chains['topics']
    
    @property
    def combined_analysis_chain(self):
        """Get the combined analysis chain, initializing if needed."""
        if not self._chains_initialized:
            self._setup_chains()
        return self._chains['combined']
    
    async def generate_summary(
        self,
        conversation_data: ConversationData,
        config: SummarizationConfig
    ) -> SummarizationResult:
        """
        Generate a comprehensive summary of a conversation.
        
        Args:
            conversation_data: Conversation data to summarize
            config: Summarization configuration
            
        Returns:
            SummarizationResult with the generated summary
        """
        start_time = datetime.now()
        
        try:
            # Prepare conversation text
            conversation_text = self._prepare_conversation_text(conversation_data)
            
            if not conversation_text.strip():
                return SummarizationResult(
                    success=False,
                    error="No conversation content to summarize",
                    processing_time=(datetime.now() - start_time).total_seconds()
                )
            
            # Count AI messages
            ai_message_count = sum(1 for msg in conversation_data.messages if msg.role == "assistant")
            
            # Prepare human agents information
            human_agents_text = self._prepare_human_agents_text(conversation_data.human_agents)
            
            # Prepare chain inputs
            chain_inputs = {
                "conversation_text": conversation_text,
                "summary_style": config.style,
                "max_length": config.max_summary_length,
                "human_agents": human_agents_text,
                "ai_message_count": ai_message_count
            }
            
            # Generate summary using individual chains
            summary = await self.summary_chain.ainvoke(chain_inputs)
            
            # Generate additional analysis if requested
            key_points = []
            sentiment = None
            sentiment_emoji = None
            topics = []
            
            if config.include_key_points:
                key_points_inputs = {
                    "conversation_text": conversation_text,
                    "ai_message_count": ai_message_count
                }
                key_points_text = await self.key_points_chain.ainvoke(key_points_inputs)
                key_points = self._parse_key_points(key_points_text)
            
            if config.include_sentiment:
                sentiment_text = await self.sentiment_chain.ainvoke({"conversation_text": conversation_text})
                sentiment, sentiment_emoji = self._parse_sentiment_with_emoji(sentiment_text)
            
            if config.include_topics:
                topics_text = await self.topics_chain.ainvoke({"conversation_text": conversation_text})
                topics = self._parse_topics(topics_text)
            
            # Calculate duration
            duration_minutes = None
            if conversation_data.start_time and conversation_data.end_time:
                duration_minutes = (conversation_data.end_time - conversation_data.start_time).total_seconds() / 60
            
            # Create response
            summary_response = ConversationSummaryResponse(
                conversation_id=conversation_data.conversation_id,
                summary=summary,
                key_points=key_points,
                sentiment=sentiment,
                sentiment_emoji=sentiment_emoji,
                topics=topics,
                metadata={
                    "style": config.style,
                    "language": config.language,
                    "max_length": config.max_summary_length
                },
                generated_at=datetime.now(),
                message_count=len(conversation_data.messages),
                ai_message_count=ai_message_count,
                human_agents=conversation_data.human_agents,
                duration_minutes=duration_minutes
            )
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            logger.info(
                f"Generated summary for conversation {conversation_data.conversation_id} "
                f"in {processing_time:.2f}s"
            )
            
            return SummarizationResult(
                success=True,
                summary=summary_response,
                processing_time=processing_time
            )
            
        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"Error generating summary: {str(e)}")
            
            return SummarizationResult(
                success=False,
                error=str(e),
                processing_time=processing_time
            )
    
    def _prepare_human_agents_text(self, human_agents: List[Dict[str, str]]) -> str:
        """
        Prepare human agents information for the prompt.
        
        Args:
            human_agents: List of human agents with name and email
            
        Returns:
            Formatted text for human agents
        """
        if not human_agents:
            return "No human agents identified in this conversation."
        
        agent_lines = []
        for agent in human_agents:
            name = agent.get("name", "Unknown")
            email = agent.get("email", "No email")
            agent_lines.append(f"- {name} ({email})")
        
        return "\n".join(agent_lines)
    
    def _prepare_conversation_text(self, conversation_data: ConversationData) -> str:
        """
        Prepare conversation text for summarization.
        
        Args:
            conversation_data: Conversation data
            
        Returns:
            Formatted conversation text
        """
        if not conversation_data.messages:
            return ""
        
        # Sort messages by timestamp
        sorted_messages = sorted(conversation_data.messages, key=lambda x: x.timestamp)
        
        conversation_lines = []
        
        for message in sorted_messages:
            # Format timestamp
            timestamp = message.timestamp.strftime("%H:%M")
            
            # Determine speaker
            if message.role == "user":
                speaker = "👤 Customer"
            elif message.role == "assistant":
                speaker = "🤖 AI Assistant"
            else:
                # For human agents, include their name if available
                if message.sender_name:
                    speaker = f"👨‍💼 {message.sender_name}"
                else:
                    speaker = f"📝 {message.role.title()}"
            
            # Format message
            message_line = f"[{timestamp}] {speaker}: {message.content}"
            conversation_lines.append(message_line)
        
        return "\n".join(conversation_lines)
    
    def _parse_key_points(self, key_points_text: str) -> List[str]:
        """
        Parse key points from LLM output.
        
        Args:
            key_points_text: Raw key points text from LLM
            
        Returns:
            List of key points
        """
        if not key_points_text:
            return []
        
        # Split by bullet points or numbered lists
        lines = key_points_text.strip().split('\n')
        key_points = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Remove bullet points, numbers, and dashes
            line = line.lstrip('•-*0123456789. ')
            
            if line and len(line) > 3:  # Minimum meaningful length
                key_points.append(line)
        
        return key_points[:10]  # Limit to 10 key points
    
    def _parse_sentiment_with_emoji(self, sentiment_text: str) -> tuple[Optional[str], Optional[str]]:
        """
        Parse sentiment and emoji from LLM output.
        
        Args:
            sentiment_text: Raw sentiment text from LLM
            
        Returns:
            Tuple of (sentiment, emoji) or (None, None)
        """
        if not sentiment_text:
            return None, None
        
        # Look for sentiment indicators
        text_lower = sentiment_text.lower()
        
        # Extract sentiment
        sentiment = None
        if "positive" in text_lower:
            sentiment = "positive"
        elif "negative" in text_lower:
            sentiment = "negative"
        elif "neutral" in text_lower:
            sentiment = "neutral"
        
        # Extract emoji
        emoji = None
        emoji_patterns = {
            "😊": ["positive", "happy", "satisfied", "pleased"],
            "😐": ["neutral", "indifferent", "calm"],
            "😞": ["negative", "disappointed", "sad"],
            "😤": ["frustrated", "annoyed", "irritated"],
            "😡": ["angry", "furious", "upset"],
            "🤔": ["confused", "uncertain", "thinking"],
            "😌": ["relieved", "content", "peaceful"],
            "😰": ["anxious", "worried", "nervous"],
            "😍": ["excited", "enthusiastic", "delighted"],
            "😔": ["sad", "disappointed", "regretful"]
        }
        
        for emoji_char, keywords in emoji_patterns.items():
            if any(keyword in text_lower for keyword in keywords):
                emoji = emoji_char
                break
        
        # If no emoji found, assign default based on sentiment
        if not emoji and sentiment:
            if sentiment == "positive":
                emoji = "😊"
            elif sentiment == "negative":
                emoji = "😞"
            else:
                emoji = "😐"
        
        return sentiment, emoji
    
    def _parse_sentiment(self, sentiment_text: str) -> Optional[str]:
        """
        Parse sentiment from LLM output (legacy method).
        
        Args:
            sentiment_text: Raw sentiment text from LLM
            
        Returns:
            Extracted sentiment or None
        """
        sentiment, _ = self._parse_sentiment_with_emoji(sentiment_text)
        return sentiment
    
    def _parse_topics(self, topics_text: str) -> List[str]:
        """
        Parse topics from LLM output.
        
        Args:
            topics_text: Raw topics text from LLM
            
        Returns:
            List of topics
        """
        if not topics_text:
            return []
        
        # Split by numbered lists or bullet points
        lines = topics_text.strip().split('\n')
        topics = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Remove numbers, bullet points, and brackets
            line = line.lstrip('0123456789.•-* ')
            line = line.replace('[', '').replace(']', '')
            
            if line and len(line) > 2:  # Minimum meaningful length
                topics.append(line)
        
        return topics[:5]  # Limit to 5 topics
