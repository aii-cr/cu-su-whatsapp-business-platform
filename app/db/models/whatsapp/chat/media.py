"""
Media model for the WhatsApp Business Platform.
Handles media files (images, audio, video, documents) with metadata and storage.
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime, timezone
from bson import ObjectId
from enum import Enum
from app.db.models.base import PyObjectId

class MediaType(str, Enum):
    """Media file types supported by WhatsApp."""
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    DOCUMENT = "document"
    STICKER = "sticker"

class MediaStatus(str, Enum):
    """Media processing status."""
    UPLOADING = "uploading"
    PROCESSING = "processing"
    READY = "ready"
    FAILED = "failed"
    DELETED = "deleted"

class StorageProvider(str, Enum):
    """Storage provider options."""
    LOCAL = "local"
    AWS_S3 = "aws_s3"
    GOOGLE_CLOUD = "google_cloud"
    AZURE_BLOB = "azure_blob"
    WHATSAPP = "whatsapp"

class Media(BaseModel):
    """
    Media model for storing file metadata and references.
    """
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    
    # Core identification
    whatsapp_media_id: Optional[str] = Field(None, description="WhatsApp media ID")
    filename: str = Field(..., description="Original filename")
    
    # File properties
    media_type: MediaType = Field(..., description="Type of media file")
    mimetype: str = Field(..., description="MIME type of the file")
    file_size: int = Field(..., ge=0, description="File size in bytes")
    
    # Storage information
    storage_provider: StorageProvider = Field(default=StorageProvider.LOCAL)
    storage_path: str = Field(..., description="Storage path or key")
    public_url: Optional[str] = Field(None, description="Public access URL")
    
    # WhatsApp specific URLs
    whatsapp_url: Optional[str] = Field(None, description="WhatsApp media URL")
    download_url: Optional[str] = Field(None, description="Direct download URL")
    
    # File metadata
    metadata: Dict[str, Any] = Field(
        default_factory=lambda: {
            "width": None,
            "height": None,
            "duration": None,
            "format": None,
            "quality": None,
            "encoding": None,
            "pages": None,
            "author": None,
            "title": None
        },
        description="Media-specific metadata"
    )
    
    # Processing status
    status: MediaStatus = Field(default=MediaStatus.UPLOADING)
    processing_status: Dict[str, Any] = Field(
        default_factory=lambda: {
            "upload_progress": 0,
            "processing_stage": None,
            "error_message": None,
            "retry_count": 0,
            "thumbnails_generated": False
        },
        description="Processing status information"
    )
    
    # Thumbnails and previews
    thumbnails: Dict[str, str] = Field(
        default_factory=dict,
        description="Generated thumbnail URLs by size"
    )
    preview_url: Optional[str] = Field(None, description="Preview image URL")
    
    # Security and validation
    is_validated: bool = Field(default=False, description="Whether file passed security validation")
    virus_scan_result: Optional[Dict[str, Any]] = Field(
        None,
        description="Virus scan results"
    )
    content_hash: Optional[str] = Field(None, description="File content hash (SHA-256)")
    
    # Access control
    is_public: bool = Field(default=False, description="Whether file is publicly accessible")
    access_permissions: Dict[str, Any] = Field(
        default_factory=lambda: {
            "users": [],
            "departments": [],
            "roles": []
        },
        description="Access control permissions"
    )
    
    # Usage tracking
    download_count: int = Field(default=0, description="Number of downloads")
    last_accessed_at: Optional[datetime] = Field(None, description="Last access timestamp")
    
    # Relationships
    conversation_id: Optional[PyObjectId] = Field(None, description="Associated conversation ID")
    message_id: Optional[PyObjectId] = Field(None, description="Associated message ID")
    uploaded_by: Optional[PyObjectId] = Field(None, description="User who uploaded the file")
    
    # Lifecycle management
    expires_at: Optional[datetime] = Field(None, description="File expiration timestamp")
    auto_delete_at: Optional[datetime] = Field(None, description="Automatic deletion timestamp")
    
    # Metadata
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    deleted_at: Optional[datetime] = Field(None, description="Soft deletion timestamp")
    
    # Tags and categorization
    tags: list[str] = Field(default_factory=list, description="Media tags")
    alt_text: Optional[str] = Field(None, max_length=500, description="Alternative text description")
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {PyObjectId: str}
        json_schema_extra = {
            "example": {
                "filename": "document.pdf",
                "media_type": "document",
                "mimetype": "application/pdf",
                "file_size": 1048576,
                "storage_provider": "local",
                "storage_path": "/uploads/documents/document.pdf",
                "conversation_id": "60a7c8b9f123456789abcdef"
            }
        }

class MediaUpload(BaseModel):
    """Schema for media upload requests."""
    filename: str
    media_type: MediaType
    mimetype: str
    file_size: int = Field(..., ge=0)
    conversation_id: Optional[str] = None
    message_id: Optional[str] = None
    tags: list[str] = Field(default_factory=list)
    alt_text: Optional[str] = Field(None, max_length=500)
    is_public: bool = False

class MediaUpdate(BaseModel):
    """Schema for updating media metadata."""
    filename: Optional[str] = None
    tags: Optional[list[str]] = None
    alt_text: Optional[str] = Field(None, max_length=500)
    is_public: Optional[bool] = None
    metadata: Optional[Dict[str, Any]] = None
    status: Optional[MediaStatus] = None
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class MediaResponse(BaseModel):
    """Schema for media responses."""
    id: str = Field(alias="_id")
    whatsapp_media_id: Optional[str]
    filename: str
    media_type: MediaType
    mimetype: str
    file_size: int
    storage_provider: StorageProvider
    public_url: Optional[str]
    download_url: Optional[str]
    metadata: Dict[str, Any]
    status: MediaStatus
    thumbnails: Dict[str, str]
    preview_url: Optional[str]
    is_validated: bool
    conversation_id: Optional[str]
    message_id: Optional[str]
    uploaded_by: Optional[str]
    download_count: int
    tags: list[str]
    alt_text: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        populate_by_name = True 