"""WhatsApp integration schemas package."""

from .webhook import (
    WebhookChallenge, WebhookEntry, WhatsAppWebhookPayload,
    ContactInfo, MessageContext, TextMessage, MediaMessage,
    ImageMessage, AudioMessage, VideoMessage, DocumentMessage,
    StickerMessage, LocationMessage, ContactMessage, InteractiveMessage,
    OrderMessage, SystemMessage, IncomingMessage, MessageStatus,
    WebhookChange, ProcessedWebhookData, WebhookProcessingResult,
    OutboundMessageRequest, WhatsAppAPIResponse, TemplateComponent,
    TemplateMessageRequest, MediaUploadResponse, WebhookSubscription,
    RateLimitInfo, WhatsAppErrorResponse
)

__all__ = [
    # Webhook schemas
    "WebhookChallenge", "WebhookEntry", "WhatsAppWebhookPayload",
    "ContactInfo", "MessageContext", "TextMessage", "MediaMessage",
    "ImageMessage", "AudioMessage", "VideoMessage", "DocumentMessage",
    "StickerMessage", "LocationMessage", "ContactMessage", "InteractiveMessage",
    "OrderMessage", "SystemMessage", "IncomingMessage", "MessageStatus",
    "WebhookChange", "ProcessedWebhookData", "WebhookProcessingResult",
    
    # API schemas
    "OutboundMessageRequest", "WhatsAppAPIResponse", "TemplateComponent",
    "TemplateMessageRequest", "MediaUploadResponse", "WebhookSubscription",
    "RateLimitInfo", "WhatsAppErrorResponse"
] 