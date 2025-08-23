"""
Configuration for RAG settings across different agents.
"""

from typing import Dict, Any


# Default RAG settings
DEFAULT_RAG_CONFIG = {
    "k": 6,  # Number of documents to retrieve
    "tenant_id": None,  # Disable tenant filtering by default
    "locale": None,  # Disable locale filtering by default
    "score_threshold": 0.2,  # Minimum relevance score
    "enable_multi_query": True,  # Enable query expansion
    "enable_compression": True,  # Enable document compression
}


# Agent-specific RAG configurations
AGENT_RAG_CONFIGS = {
    "whatsapp": {
        **DEFAULT_RAG_CONFIG,
        "max_context_length": 4000,  # WhatsApp-specific context limit
        "default_locale": "es_CR",  # Default locale for WhatsApp
        "response_format": "whatsapp",  # WhatsApp-specific response formatting
    },
    "writer": {
        **DEFAULT_RAG_CONFIG,
        "max_context_length": 8000,  # Writer can handle longer context
        "default_locale": None,  # No default locale for writer
        "response_format": "detailed",  # Detailed response formatting
    }
}


def get_rag_config(agent_name: str = "default") -> Dict[str, Any]:
    """
    Get RAG configuration for a specific agent.
    
    Args:
        agent_name: Name of the agent (whatsapp, writer, etc.)
        
    Returns:
        Dictionary with RAG configuration
    """
    return AGENT_RAG_CONFIGS.get(agent_name, DEFAULT_RAG_CONFIG)


def get_rag_config_for_agent(agent_name: str, **overrides) -> Dict[str, Any]:
    """
    Get RAG configuration for a specific agent with optional overrides.
    
    Args:
        agent_name: Name of the agent
        **overrides: Configuration overrides
        
    Returns:
        Dictionary with RAG configuration
    """
    config = get_rag_config(agent_name).copy()
    config.update(overrides)
    return config
