"""
Prompts for conversation summarization.
"""

from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser


# Main summarization prompt
CONVERSATION_SUMMARY_PROMPT = PromptTemplate(
    input_variables=["conversation_text", "summary_style", "max_length", "human_agents", "ai_message_count"],
    template="""You are an expert conversation analyst. Your task is to create a comprehensive summary of a WhatsApp conversation.

CONVERSATION PARTICIPANTS:
{human_agents}

AI ASSISTANT MESSAGES: {ai_message_count} messages were sent by the AI assistant.

CONVERSATION:
{conversation_text}

INSTRUCTIONS:
- Create a {summary_style} summary of the conversation
- Start with a clear list of all human agents involved (full names and emails)
- Include the AI assistant message count as the first insight
- Focus on the main topics, key decisions, and important information exchanged
- Include relevant context and background information
- Keep the summary under {max_length} words
- Use clear, professional language
- Structure the summary with appropriate headings and bullet points
- Highlight any action items, questions, or unresolved issues
- Maintain chronological order of important events

SUMMARY:"""
)


# Key points extraction prompt
KEY_POINTS_PROMPT = PromptTemplate(
    input_variables=["conversation_text", "ai_message_count"],
    template="""Extract the key points from this conversation. Focus on:
- AI assistant involvement ({ai_message_count} messages sent)
- Main topics discussed
- Important decisions made
- Action items or next steps
- Questions asked and answered
- Any issues or concerns raised

CONVERSATION:
{conversation_text}

KEY POINTS:
- """
)





# Topic extraction prompt
TOPIC_EXTRACTION_PROMPT = PromptTemplate(
    input_variables=["conversation_text"],
    template="""Identify the main topics discussed in this conversation. Extract topics that are:
- Explicitly mentioned
- Implicitly discussed
- Related to business or customer service

CONVERSATION:
{conversation_text}

MAIN TOPICS:
1. [Topic 1]
2. [Topic 2]
3. [Topic 3]
..."""
)


# Detailed analysis prompt
DETAILED_ANALYSIS_PROMPT = PromptTemplate(
    input_variables=["conversation_text", "analysis_type"],
    template="""Provide a detailed {analysis_type} analysis of this conversation.

CONVERSATION:
{conversation_text}

ANALYSIS TYPE: {analysis_type}

Please provide a comprehensive analysis focusing on:
- Main themes and patterns
- Customer needs and pain points
- Agent performance and response quality
- Resolution effectiveness
- Areas for improvement
"""
)


# Executive summary prompt
EXECUTIVE_SUMMARY_PROMPT = PromptTemplate(
    input_variables=["conversation_text"],
    template="""Create an executive summary of this customer conversation for management review.

CONVERSATION:
{conversation_text}

EXECUTIVE SUMMARY:
Please provide a concise summary that includes:
- Customer issue or inquiry
- Resolution or outcome
- Customer satisfaction level
- Any escalations or special handling required
- Key metrics or insights for management

EXECUTIVE SUMMARY:"""
)


# Technical summary prompt
TECHNICAL_SUMMARY_PROMPT = PromptTemplate(
    input_variables=["conversation_text"],
    template="""Create a technical summary of this conversation for technical teams.

CONVERSATION:
{conversation_text}

TECHNICAL SUMMARY:
Please provide a technical analysis that includes:
- Technical issues discussed
- System or product problems mentioned
- Technical solutions provided
- Required follow-up actions
- Impact assessment
- Technical recommendations

TECHNICAL SUMMARY:"""
)


# Customer service summary prompt
CUSTOMER_SERVICE_SUMMARY_PROMPT = PromptTemplate(
    input_variables=["conversation_text"],
    template="""Create a customer service summary of this conversation.

CONVERSATION:
{conversation_text}

CUSTOMER SERVICE SUMMARY:
Please provide a summary that includes:
- Customer inquiry or issue
- Service provided
- Customer satisfaction indicators
- Response time and quality
- Follow-up requirements
- Service improvement opportunities

CUSTOMER SERVICE SUMMARY:"""
)


def get_summary_prompt() -> PromptTemplate:
    """Get the main summary prompt."""
    return CONVERSATION_SUMMARY_PROMPT


def get_key_points_prompt() -> PromptTemplate:
    """Get the key points extraction prompt."""
    return KEY_POINTS_PROMPT

def get_topics_prompt() -> PromptTemplate:
    """Get the topic extraction prompt."""
    return TOPIC_EXTRACTION_PROMPT


def get_detailed_analysis_prompt() -> PromptTemplate:
    """Get the detailed analysis prompt."""
    return DETAILED_ANALYSIS_PROMPT
