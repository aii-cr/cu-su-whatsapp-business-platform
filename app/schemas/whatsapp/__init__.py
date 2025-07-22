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

from .chat import (
    ConversationCreate, ConversationUpdate, ConversationTransfer, ConversationClose,
    ConversationResponse, ConversationDetailResponse, ConversationListResponse,
    ConversationQueryParams, ConversationAssignment, ConversationTagUpdate,
    ConversationBulkAction, ConversationStatsResponse, ConversationActivity,
    ConversationSLAStatus, MessageCreate, TextMessageCreate, MediaMessageCreate, 
    TemplateMessageCreate, LocationMessageCreate, ContactMessageCreate, 
    InteractiveMessageCreate, MessageUpdate, MessageResponse, MessageDetailResponse, 
    MessageListResponse, MessageQueryParams, MessageStatusUpdate, BulkMessageStatusUpdate,
    MessageReadReceipt, MessageStatsResponse, MessageContentValidation,
    MessageSearchParams, MessageExportRequest, QuickReply, MessageReaction,
    WhatsAppWebhookMessage, MediaUpload, MediaUpdate, MediaResponse, MediaListResponse,
    MediaQueryParams, MediaDownloadRequest, MediaUploadProgress,
    BulkMediaDelete, BulkMediaTagUpdate, MediaStatsResponse,
    MediaValidationResponse, MediaProcessingJob, TagCreate, TagUpdate, TagResponse, 
    TagListResponse, GroupedTagsResponse, TagQueryParams, TagAssignment, TagRemoval, 
    BulkTagAssignment, TagStatsResponse, TagUsageAnalytics, TagAutoAssignRule, 
    TagExportRequest, NoteCreate, NoteUpdate, NoteResponse, NoteDetailResponse, 
    NoteListResponse, NoteQueryParams, NotePinToggle, BulkNoteDelete, BulkNoteTagUpdate,
    NoteTemplate, NoteStatsResponse, NoteReminder, NoteActivity, NoteExportRequest
)

__all__ = [
    # Webhook schemas
    "WebhookChallenge", "WebhookEntry", "WhatsAppWebhookPayload",
    "ContactInfo", "MessageContext", "TextMessage", "MediaMessage",
    "ImageMessage", "AudioMessage", "VideoMessage", "DocumentMessage",
    "StickerMessage", "LocationMessage", "ContactMessage", "InteractiveMessage",
    "OrderMessage", "SystemMessage", "IncomingMessage", "MessageStatus",
    "WebhookChange", "ProcessedWebhookData", "WebhookProcessingResult",
    "OutboundMessageRequest", "WhatsAppAPIResponse", "TemplateComponent",
    "TemplateMessageRequest", "MediaUploadResponse", "WebhookSubscription",
    "RateLimitInfo", "WhatsAppErrorResponse",
    
    # Chat schemas
    "ConversationCreate", "ConversationUpdate", "ConversationTransfer", "ConversationClose",
    "ConversationResponse", "ConversationDetailResponse", "ConversationListResponse",
    "ConversationQueryParams", "ConversationAssignment", "ConversationTagUpdate",
    "ConversationBulkAction", "ConversationStatsResponse", "ConversationActivity",
    "ConversationSLAStatus", "MessageCreate", "TextMessageCreate", "MediaMessageCreate", 
    "TemplateMessageCreate", "LocationMessageCreate", "ContactMessageCreate", 
    "InteractiveMessageCreate", "MessageUpdate", "MessageResponse", "MessageDetailResponse", 
    "MessageListResponse", "MessageQueryParams", "MessageStatusUpdate", "BulkMessageStatusUpdate",
    "MessageReadReceipt", "MessageStatsResponse", "MessageContentValidation",
    "MessageSearchParams", "MessageExportRequest", "QuickReply", "MessageReaction",
    "WhatsAppWebhookMessage", "MediaUpload", "MediaUpdate", "MediaResponse", "MediaListResponse",
    "MediaQueryParams", "MediaDownloadRequest", "MediaUploadProgress",
    "BulkMediaDelete", "BulkMediaTagUpdate", "MediaStatsResponse",
    "MediaValidationResponse", "MediaProcessingJob", "TagCreate", "TagUpdate", "TagResponse", 
    "TagListResponse", "GroupedTagsResponse", "TagQueryParams", "TagAssignment", "TagRemoval", 
    "BulkTagAssignment", "TagStatsResponse", "TagUsageAnalytics", "TagAutoAssignRule", 
    "TagExportRequest", "NoteCreate", "NoteUpdate", "NoteResponse", "NoteDetailResponse", 
    "NoteListResponse", "NoteQueryParams", "NotePinToggle", "BulkNoteDelete", "BulkNoteTagUpdate",
    "NoteTemplate", "NoteStatsResponse", "NoteReminder", "NoteActivity", "NoteExportRequest"
] 