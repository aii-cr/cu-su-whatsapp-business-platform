"""WhatsApp Message Service Module.

Expose both the service class and the shared singleton instance to
prevent import mistakes in other modules.
"""

from .message_service import MessageService, message_service

__all__ = ["MessageService", "message_service"]