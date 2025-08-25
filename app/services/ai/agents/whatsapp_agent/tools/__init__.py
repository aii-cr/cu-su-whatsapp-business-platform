"""
Email tools for WhatsApp agent.
"""

from .emailer import (
    send_confirmation_email,
    send_confirmation_email_with_auto_number,
    generate_confirmation_number,
)

__all__ = [
    "send_confirmation_email",
    "send_confirmation_email_with_auto_number", 
    "generate_confirmation_number",
]
