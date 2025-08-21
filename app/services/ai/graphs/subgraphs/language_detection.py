"""
Language detection and greeting subgraph.
Detects customer language and handles greeting logic.
"""

import re
from typing import Dict, Any
from app.core.logger import logger


def detect_language(text: str) -> str:
    """
    Detect language from text content.
    Simple rule-based detection for Spanish/English.
    
    Args:
        text: Input text to analyze
        
    Returns:
        Language code ('es' or 'en')
    """
    text_lower = text.lower()
    
    # Spanish indicators
    spanish_patterns = [
        r'\b(hola|buenas|gracias|por favor|ayuda|información|necesito|quiero|puedo|cómo|qué|dónde|cuándo)\b',
        r'\b(sí|no|también|muy|más|menos|mejor|peor|grande|pequeño)\b',
        r'\b(reserva|pago|precio|horario|disponibilidad)\b',
        r'[ñáéíóúü]',  # Spanish-specific characters
    ]
    
    # English indicators  
    english_patterns = [
        r'\b(hello|hi|thanks|please|help|information|need|want|can|how|what|where|when)\b',
        r'\b(yes|no|also|very|more|less|better|worse|big|small)\b',
        r'\b(booking|payment|price|schedule|availability)\b',
    ]
    
    spanish_score = 0
    english_score = 0
    
    # Check patterns
    for pattern in spanish_patterns:
        spanish_score += len(re.findall(pattern, text_lower))
    
    for pattern in english_patterns:
        english_score += len(re.findall(pattern, text_lower))
    
    # Default to Spanish for Costa Rica if unclear
    if spanish_score > english_score:
        return "es"
    elif english_score > spanish_score:
        return "en" 
    else:
        # Check for specific Spanish words that are strong indicators
        strong_spanish = ['hola', 'gracias', 'ayuda', 'información', 'reserva']
        if any(word in text_lower for word in strong_spanish):
            return "es"
        
        # Default to Spanish for Costa Rican market
        return "es"


async def detect_language_and_greeting(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Detect customer language and prepare greeting if needed.
    
    Args:
        state: Agent state dictionary
        
    Returns:
        Updated state with language detection
    """
    state["node_history"] = state.get("node_history", []) + ["detect_language"]
    
    user_text = state.get("user_text", "")
    
    # Detect language
    detected_language = detect_language(user_text)
    state["customer_language"] = detected_language
    
    logger.info(
        f"Detected language: {detected_language} for text: '{user_text[:50]}...'"
    )
    
    return state
