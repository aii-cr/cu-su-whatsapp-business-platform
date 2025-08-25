"""
Timezone utilities for Costa Rica context in WhatsApp agent.
Provides current time information for contextually appropriate greetings.
"""

from datetime import datetime
import pytz
from typing import Dict

# Costa Rica timezone
CR_TIMEZONE = pytz.timezone('America/Costa_Rica')


def get_costa_rica_time() -> datetime:
    """Get current time in Costa Rica timezone."""
    return datetime.now(CR_TIMEZONE)


def get_time_of_day_greeting(language: str = "en") -> str:
    """
    Get appropriate greeting based on current time in Costa Rica.
    
    Args:
        language: Target language ('es' or 'en')
        
    Returns:
        Appropriate greeting for the time of day
    """
    cr_time = get_costa_rica_time()
    hour = cr_time.hour
    
    if language == "en":
        if 5 <= hour < 12:
            return "Good morning"
        elif 12 <= hour < 18:
            return "Good afternoon"
        else:
            return "Good evening"
    else:  # Spanish
        if 5 <= hour < 12:
            return "Buenos días"
        elif 12 <= hour < 18:
            return "Buenas tardes"
        else:
            return "Buenas noches"


def get_current_time_context(language: str = "en") -> Dict[str, str]:
    """
    Get comprehensive time context for Costa Rica.
    
    Args:
        language: Target language ('es' or 'en')
        
    Returns:
        Dictionary with time context information
    """
    cr_time = get_costa_rica_time()
    
    # Format time for display
    formatted_time = cr_time.strftime("%H:%M")
    formatted_date = cr_time.strftime("%Y-%m-%d")
    
    # Day of week
    weekday_es = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
    weekday_en = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    
    weekday = weekday_en[cr_time.weekday()] if language == "en" else weekday_es[cr_time.weekday()]
    
    # Time period
    hour = cr_time.hour
    if language == "en":
        if 5 <= hour < 12:
            period = "morning"
        elif 12 <= hour < 18:
            period = "afternoon"
        else:
            period = "evening/night"
    else:
        if 5 <= hour < 12:
            period = "mañana"
        elif 12 <= hour < 18:
            period = "tarde"
        else:
            period = "noche"
    
    return {
        "current_time": formatted_time,
        "current_date": formatted_date,
        "weekday": weekday,
        "period": period,
        "greeting": get_time_of_day_greeting(language),
        "timezone": "Costa Rica (UTC-6)"
    }


def get_contextual_time_info(language: str = "en") -> str:
    """
    Get formatted time context string for system prompt.
    
    Args:
        language: Target language ('es' or 'en')
        
    Returns:
        Formatted string with current time context
    """
    context = get_current_time_context(language)
    
    if language == "en":
        return (
            f"Current time in Costa Rica: {context['current_time']} ({context['weekday']}, {context['period']}). "
            f"Use appropriate greeting: '{context['greeting']}' for this time of day."
        )
    else:
        return (
            f"Hora actual en Costa Rica: {context['current_time']} ({context['weekday']}, {context['period']}). "
            f"Usa el saludo apropiado: '{context['greeting']}' para esta hora del día."
        )


# For testing purposes
if __name__ == "__main__":
    print("Costa Rica Time Context:")
    print("="*50)
    
    # Test English (default)
    print("\nEnglish context:")
    print(get_contextual_time_info("en"))
    print(f"Current context: {get_current_time_context('en')}")
    
    # Test Spanish  
    print("\nSpanish context:")
    print(get_contextual_time_info("es"))
    print(f"Current context: {get_current_time_context('es')}")
