"""
Timezone utilities for Costa Rica context in WhatsApp agent.
Simplified: provide today's date in English only for prompt context.
"""

from datetime import datetime
import pytz
from typing import Dict

# Costa Rica timezone
CR_TIMEZONE = pytz.timezone('America/Costa_Rica')


def get_costa_rica_time() -> datetime:
    """Get current time in Costa Rica timezone."""
    return datetime.now(CR_TIMEZONE)


def get_today_date_en() -> str:
    """
    Get today's date in Costa Rica in English, formatted as 'Month D, YYYY'.
    Removes leading zero from the day for portability across platforms.
    """
    cr_time = get_costa_rica_time()
    day = str(int(cr_time.strftime("%d")))
    return f"{cr_time.strftime('%B')} {day}, {cr_time.strftime('%Y')}"


def get_current_time_context(language: str = "en") -> Dict[str, str]:
    """
    Backward-compatible function. Returns a minimal dict keeping only the date.
    """
    cr_time = get_costa_rica_time()
    return {
        "current_time": cr_time.strftime("%H:%M"),
        "current_date": cr_time.strftime("%Y-%m-%d"),
        "weekday": cr_time.strftime("%A"),
        "period": "",
        "greeting": "",
        "timezone": "Costa Rica (UTC-6)",
    }


def get_contextual_time_info(language: str = "en") -> str:
    """
    Backward-compatible formatter. Returns only today's date in English.
    """
    return get_today_date_en()


# For testing purposes
if __name__ == "__main__":
    print("Costa Rica Date Context:")
    print("="*50)
    print(get_contextual_time_info("en"))
