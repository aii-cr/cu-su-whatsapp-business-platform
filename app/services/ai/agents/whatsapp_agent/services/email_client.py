"""
Email client using the EmailSender service with SMTP configuration.
"""

from __future__ import annotations
import uuid
import asyncio
from typing import Optional, Sequence
from app.core.logger import logger
from app.core.config import settings
from app.services.email.email_sender import EmailSender

class EmailClient:
    def __init__(self):
        # Initialize EmailSender with SMTP credentials from config
        self.email_sender = EmailSender(
            username=settings.SMTP_PAY_USERNAME,
            password=settings.SMTP_PAY_PASSWORD,
            smtp_server=settings.SMTP_PAY_SERVER,
            port=settings.SMTP_PAY_PORT,
            use_tls=True,
            use_ssl=False,
            custom_hostname="mail.local"
        )
        self.sender_email = settings.SMTP_PAY_USERNAME

    def generate_confirmation_number(self) -> str:
        """
        Generate a unique confirmation number for bookings.
        
        Returns:
            str: Unique confirmation number in format ADN-XXXX-XXXX
        """
        # Generate a UUID and take first 8 characters
        unique_id = str(uuid.uuid4()).replace('-', '')[:8].upper()
        # Format as ADN-XXXX-XXXX
        return f"ADN-{unique_id[:4]}-{unique_id[4:8]}"

    async def send(self, to: str, subject: str, text: str, cc: Optional[Sequence[str]] = None) -> bool:
        """
        Send email using the EmailSender service.
        
        Args:
            to: Recipient email address
            subject: Email subject
            text: Email body text
            cc: Optional CC recipients
            
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        try:
            logger.info(f"[EMAIL] Sending to {to} | subject='{subject}'")
            
            # Convert to list for EmailSender
            to_addrs = [to] if isinstance(to, str) else list(to)
            cc_addrs = list(cc) if cc else None
            
            # Run the synchronous email sending in a thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                self._send_sync,
                subject,
                text,
                to_addrs,
                cc_addrs
            )
            
            logger.info(f"[EMAIL] Successfully sent to {to}")
            return True
            
        except Exception as e:
            logger.error(f"[EMAIL] Failed to send email to {to}: {e}")
            return False

    def _send_sync(self, subject: str, text: str, to_addrs: list[str], cc_addrs: Optional[list[str]] = None) -> None:
        """
        Synchronous method to send email (called from async context).
        """
        self.email_sender.send_email(
            subject=subject,
            body=text,
            to_addrs=to_addrs,
            from_addr=self.sender_email,
            cc_addrs=cc_addrs
        )

    async def send_html_email(self, to: str, subject: str, html_content: str, cc: Optional[Sequence[str]] = None) -> bool:
        """
        Send HTML email using the EmailSender service.
        
        Args:
            to: Recipient email address
            subject: Email subject
            html_content: HTML email body
            cc: Optional CC recipients
            
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        try:
            logger.info(f"[EMAIL] Sending HTML email to {to} | subject='{subject}'")
            
            # Convert to list for EmailSender
            to_addrs = [to] if isinstance(to, str) else list(to)
            cc_addrs = list(cc) if cc else None
            
            # Run the synchronous email sending in a thread pool
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                self._send_html_sync,
                subject,
                html_content,
                to_addrs,
                cc_addrs
            )
            
            logger.info(f"[EMAIL] Successfully sent HTML email to {to}")
            return True
            
        except Exception as e:
            logger.error(f"[EMAIL] Failed to send HTML email to {to}: {e}")
            return False

    def _send_html_sync(self, subject: str, html_content: str, to_addrs: list[str], cc_addrs: Optional[list[str]] = None) -> None:
        """
        Synchronous method to send HTML email (called from async context).
        """
        self.email_sender.send_html_email(
            subject=subject,
            html_body=html_content,
            to_addrs=to_addrs,
            from_addr=self.sender_email,
            cc_addrs=cc_addrs
        )

# Global email client instance
email_client = EmailClient()
