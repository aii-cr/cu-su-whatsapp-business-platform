# NEW CODE
"""
Minimal email abstraction. Change the implementation to your real provider.
"""

from __future__ import annotations
from typing import Optional, Sequence
from app.core.logger import logger

class EmailClient:
    def __init__(self, sender: str = "no-reply@american-data.cr"):
        self.sender = sender

    async def send(self, to: str, subject: str, text: str, cc: Optional[Sequence[str]] = None) -> bool:
        # TODO: replace with your real integration (SES, SendGrid, SMTP)
        try:
            logger.info(f"[EMAIL] Sending to {to} | subject='{subject}'\n{text}")
            return True
        except Exception as e:
            logger.error(f"[EMAIL] Failed: {e}")
            return False

email_client = EmailClient()
