"""
LangChain chains for conversation summarization.
"""

import asyncio
from typing import Dict, Any, List, Optional, Literal
from datetime import datetime
from operator import itemgetter

from langchain_core.language_models import BaseLanguageModel
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from app.core.logger import logger
from app.services.ai.config import ai_config
from app.core.config import settings
from app.services.ai.agents.conversation_summarizer.prompts.summarization_prompts import (
    get_summary_prompt,
    get_key_points_prompt,
    get_topics_prompt
)
from app.services.ai.agents.conversation_summarizer.schemas import (
    ConversationData,
    SummarizationConfig,
    SummarizationResult,
    ConversationSummaryResponse
)


class CombinedSummarySchema(BaseModel):
    """Validated schema returned by a single LLM call for all summary artifacts."""
    summary: str = Field(..., description="Concise, faithful conversation summary.")
    key_points: List[str] = Field(..., description="Top actionable bullet points, max 10.")
    topics: List[str] = Field(..., description="Up to 5 concise topics covered.")


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
        """
        Build a single structured-output chain that returns all artifacts in one call.
        This follows LangChain guidance to reduce round-trips and latency.
        """
        if self._chains_initialized:
            return

        llm = self._get_llm()

        # Structured-output LLM (model will be constrained to emit the schema)
        # Docs: with_structured_output() for reliable JSON/object outputs.
        # https://python.langchain.com/docs/how_to/structured_output/
        s_llm = llm.with_structured_output(CombinedSummarySchema)

        # Compact system+user prompt. Keep instructions minimal for speed.
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are a precise conversation summarizer for customer support dialogs. "
                    "Follow the schema exactly and be faithful to the provided transcript. "
                    "Do not invent facts.",
                ),
                (
                    "user",
                    "Transcript:\n{conversation_text}\n\n"
                    "Style: {summary_style}\n"
                    "Max summary length (chars): {max_length}\n"
                    "Human agents:\n{human_agents}\n"
                    "AI message count: {ai_message_count}\n"
                    "Return a concise summary, key points (<=10), and topics (<=5)."
                ),
            ]
        )

        # Single-call chain: prompt -> structured LLM -> validated object
        self._chains["combined"] = (
            {
                "conversation_text": itemgetter("conversation_text"),
                "summary_style": itemgetter("summary_style"),
                "max_length": itemgetter("max_length"),
                "human_agents": itemgetter("human_agents"),
                "ai_message_count": itemgetter("ai_message_count"),
            }
            | prompt
            | s_llm
        )

        self._chains_initialized = True
    
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
        Generate a comprehensive summary of a conversation via a single structured LLM call.
        """
        start_time = datetime.now()

        try:
            conversation_text = self._prepare_conversation_text(conversation_data)
            if not conversation_text.strip():
                return SummarizationResult(
                    success=False,
                    error="No conversation content to summarize",
                    processing_time=(datetime.now() - start_time).total_seconds(),
                )

            ai_message_count = sum(
                1 for msg in conversation_data.messages if msg.role == "ai_assistant"
            )
            human_agents_text = self._prepare_human_agents_text(conversation_data.human_agents)

            chain_inputs = {
                "conversation_text": conversation_text,
                "summary_style": config.style,
                "max_length": config.max_summary_length,
                "human_agents": human_agents_text,
                "ai_message_count": ai_message_count,
            }

            # One fast, validated call returning all fields.
            combined = await self.combined_analysis_chain.ainvoke(chain_inputs)

            # Duration in minutes if timestamps are present
            duration_minutes = None
            if conversation_data.start_time and conversation_data.end_time:
                duration_minutes = (
                    (conversation_data.end_time - conversation_data.start_time).total_seconds() / 60
                )

            summary_response = ConversationSummaryResponse(
                conversation_id=conversation_data.conversation_id,
                summary=combined.summary,
                key_points=combined.key_points if config.include_key_points else [],
                topics=combined.topics if config.include_topics else [],
                metadata={
                    "style": config.style,
                    "language": config.language,
                    "max_length": config.max_summary_length,
                    # Include sentiment data from conversation metadata
                    "current_sentiment_emoji": conversation_data.metadata.get("current_sentiment_emoji"),
                    "sentiment_confidence": conversation_data.metadata.get("sentiment_confidence"),
                    "last_sentiment_analysis_at": conversation_data.metadata.get("last_sentiment_analysis_at")
                },
                generated_at=datetime.now(),
                message_count=len(conversation_data.messages),
                ai_message_count=ai_message_count,
                human_agents=conversation_data.human_agents,
                customer=conversation_data.customer,
                duration_minutes=duration_minutes,
            )

            processing_time = (datetime.now() - start_time).total_seconds()
            logger.info(
                f"Generated summary for conversation {conversation_data.conversation_id} "
                f"in {processing_time:.2f}s (single-call structured output)"
            )

            return SummarizationResult(
                success=True, summary=summary_response, processing_time=processing_time
            )

        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"Error generating summary: {str(e)}")
            return SummarizationResult(success=False, error=str(e), processing_time=processing_time)
    
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
            if message.role == "customer":
                speaker = "👤 Customer"
            elif message.role == "ai_assistant":
                speaker = "🤖 AI Assistant"
            elif message.role == "agent":
                # For human agents, include their name if available
                if message.sender_name:
                    speaker = f"👨‍💼 {message.sender_name}"
                else:
                    speaker = f"👨‍💼 Agent"
            else:
                speaker = f"📝 {message.role.title()}"
            
            # Format message
            message_line = f"[{timestamp}] {speaker}: {message.content}"
            conversation_lines.append(message_line)
        
        return "\n".join(conversation_lines)
