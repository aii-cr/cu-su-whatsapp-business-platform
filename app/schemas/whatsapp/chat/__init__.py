"""WhatsApp chat and messaging schemas package."""

from .conversation import (
    ConversationCreate, ConversationUpdate, ConversationTransfer, ConversationClose,
    ConversationResponse, ConversationDetailResponse, ConversationListResponse,
    ConversationQueryParams, ConversationAssignment, ConversationTagUpdate,
    ConversationBulkAction, ConversationStatsResponse, ConversationActivity,
    ConversationSLAStatus
)

from .message import (
    MessageCreate, MessageUpdate, MessageSend, MessageReadRequest, MessageReadResponse,
    MessageResponse, MessageListResponse, MessageStatusUpdate
)
from .message_in import *
from .message_out import *

from .media import (
    MediaUpload, MediaUpdate, MediaResponse, MediaListResponse,
    MediaQueryParams, MediaDownloadRequest, MediaUploadProgress,
    BulkMediaDelete, BulkMediaTagUpdate, MediaStatsResponse,
    MediaValidationResponse, MediaProcessingJob
)

from .tag import (
    TagCreate, TagAssign, TagUnassign, TagResponse, TagSearchResponse,
    ConversationTagResponse, TagOperationResponse
)

from .note import (
    NoteCreate, NoteUpdate, NoteResponse, NoteDetailResponse, NoteListResponse,
    NoteQueryParams, NotePinToggle, BulkNoteDelete, BulkNoteTagUpdate,
    NoteTemplate, NoteStatsResponse, NoteReminder, NoteActivity, NoteExportRequest
)

__all__ = [
    # Conversation schemas
    "ConversationCreate", "ConversationUpdate", "ConversationTransfer", "ConversationClose",
    "ConversationResponse", "ConversationDetailResponse", "ConversationListResponse",
    "ConversationQueryParams", "ConversationAssignment", "ConversationTagUpdate",
    "ConversationBulkAction", "ConversationStatsResponse", "ConversationActivity",
    "ConversationSLAStatus",
    
    # Message schemas
    "MessageCreate", "MessageUpdate", "MessageSend", "MessageReadRequest", "MessageReadResponse",
    "MessageResponse", "MessageListResponse", "MessageStatusUpdate",
    
    # Media schemas
    "MediaUpload", "MediaUpdate", "MediaResponse", "MediaListResponse",
    "MediaQueryParams", "MediaDownloadRequest", "MediaUploadProgress",
    "BulkMediaDelete", "BulkMediaTagUpdate", "MediaStatsResponse",
    "MediaValidationResponse", "MediaProcessingJob",
    
    # Tag schemas
    "TagCreate", "TagAssign", "TagUnassign", "TagResponse", "TagSearchResponse",
    "ConversationTagResponse", "TagOperationResponse",
    
    # Note schemas
    "NoteCreate", "NoteUpdate", "NoteResponse", "NoteDetailResponse", "NoteListResponse",
    "NoteQueryParams", "NotePinToggle", "BulkNoteDelete", "BulkNoteTagUpdate",
    "NoteTemplate", "NoteStatsResponse", "NoteReminder", "NoteActivity", "NoteExportRequest"
] 