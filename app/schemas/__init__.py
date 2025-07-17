"""
Comprehensive request/response schemas package with organized submodules.

Schemas are organized into logical categories:
- auth: Authentication and authorization schemas
- chat: Messaging and conversation schemas  
- business: Organization and company schemas
- system: System and compliance schemas
- whatsapp: WhatsApp API integration schemas
"""

# Import from organized subpackages
from .auth import *
from .chat import *
from .business import *
from .system import *
from .whatsapp import *

# Re-export commonly used schemas
from .auth import (
    UserRegister, UserLogin, UserResponse, TokenResponse,
    RoleCreate, RoleResponse, PermissionResponse
)
from .chat import (
    ConversationCreate, ConversationResponse, ConversationListResponse,
    MessageCreate, MessageResponse, MessageListResponse,
    MediaUpload, MediaResponse, TagCreate, TagResponse, NoteCreate, NoteResponse
)
from .business import (
    DepartmentCreate, DepartmentResponse, CompanyProfileUpdate, CompanyProfileResponse
)
from .whatsapp import (
    WhatsAppWebhookPayload, IncomingMessage, OutboundMessageRequest, WebhookChallenge
)

# Common response schemas
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class SuccessResponse(BaseModel):
    """Standard success response."""
    success: bool = True
    message: str = "Operation completed successfully"
    data: Optional[Dict[str, Any]] = None

class ErrorResponse(BaseModel):
    """Standard error response."""
    success: bool = False
    error_code: str
    error_message: str
    details: Optional[Dict[str, Any]] = None

class PaginatedResponse(BaseModel):
    """Standard paginated response."""
    items: List[Any]
    total: int
    page: int
    per_page: int
    pages: int
    has_next: bool
    has_prev: bool

class HealthCheckResponse(BaseModel):
    """Health check response."""
    status: str
    timestamp: str
    version: str
    database: str
    services: Dict[str, str]
