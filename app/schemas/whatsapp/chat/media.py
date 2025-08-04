"""Media-related request/response schemas."""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from app.db.models.base import PyObjectId

# Media Upload Request
class MediaUpload(BaseModel):
    conversation_id: Optional[PyObjectId] = Field(None, description="Associated conversation ID")
    file_name: str = Field(..., description="Original file name")
    file_size: int = Field(..., gt=0, description="File size in bytes")
    mime_type: str = Field(..., description="MIME type of the file")
    description: Optional[str] = Field(None, max_length=500, description="Media description")
    alt_text: Optional[str] = Field(None, max_length=100, description="Alternative text for accessibility")
    
    @validator('file_size')
    def validate_file_size(cls, v, values):
        mime_type = values.get('mime_type', '')
        
        # Size limits based on WhatsApp restrictions
        if mime_type.startswith('image/'):
            max_size = 5 * 1024 * 1024  # 5MB
        elif mime_type.startswith('audio/') or mime_type.startswith('video/'):
            max_size = 16 * 1024 * 1024  # 16MB
        elif mime_type.startswith('application/'):
            max_size = 100 * 1024 * 1024  # 100MB
        else:
            max_size = 16 * 1024 * 1024  # Default 16MB
            
        if v > max_size:
            raise ValueError(f'File size exceeds maximum allowed size for {mime_type}')
        return v

# Media Update
class MediaUpdate(BaseModel):
    description: Optional[str] = Field(None, max_length=500, description="Updated media description")
    alt_text: Optional[str] = Field(None, max_length=100, description="Updated alternative text")
    tags: Optional[List[str]] = Field(None, description="Updated media tags")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Updated metadata")

# Media Response
class MediaResponse(BaseModel):
    id: PyObjectId = Field(alias="_id")
    conversation_id: Optional[PyObjectId] = None
    whatsapp_media_id: Optional[str] = None
    file_name: str
    original_name: str
    file_size: int
    mime_type: str
    media_type: str  # image, audio, video, document
    file_path: str
    url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    status: str  # uploading, processing, ready, failed
    storage_provider: str
    description: Optional[str] = None
    alt_text: Optional[str] = None
    duration: Optional[int] = None  # For audio/video in seconds
    dimensions: Optional[Dict[str, int]] = None  # width, height for images/videos
    virus_scan_status: str  # pending, clean, infected, failed
    created_at: datetime
    updated_at: datetime
    expires_at: Optional[datetime] = None
    download_count: int = 0
    tags: List[str] = []
    metadata: Dict[str, Any] = {}

    class Config:
        populate_by_name = True
        json_encoders = {
            PyObjectId: str,
            datetime: lambda v: v.isoformat()
        }

# Media List Response
class MediaListResponse(BaseModel):
    media: List[MediaResponse]
    total: int
    page: int
    per_page: int
    pages: int

# Media Query Parameters
class MediaQueryParams(BaseModel):
    page: int = Field(1, ge=1, description="Page number")
    per_page: int = Field(20, ge=1, le=100, description="Items per page")
    conversation_id: Optional[PyObjectId] = Field(None, description="Filter by conversation")
    media_type: Optional[str] = Field(None, description="Filter by media type")
    mime_type: Optional[str] = Field(None, description="Filter by MIME type")
    status: Optional[str] = Field(None, description="Filter by status")
    storage_provider: Optional[str] = Field(None, description="Filter by storage provider")
    virus_scan_status: Optional[str] = Field(None, description="Filter by virus scan status")
    from_date: Optional[datetime] = Field(None, description="Filter media from this date")
    to_date: Optional[datetime] = Field(None, description="Filter media to this date")
    min_size: Optional[int] = Field(None, description="Minimum file size")
    max_size: Optional[int] = Field(None, description="Maximum file size")
    tags: Optional[List[str]] = Field(None, description="Filter by tags")
    search: Optional[str] = Field(None, description="Search in file name or description")
    sort_by: str = Field("created_at", description="Sort field")
    sort_order: str = Field("desc", pattern="^(asc|desc)$", description="Sort order")

# Media Download Request
class MediaDownloadRequest(BaseModel):
    media_id: PyObjectId = Field(..., description="Media ID to download")
    generate_thumbnail: bool = Field(False, description="Generate thumbnail if applicable")
    quality: Optional[str] = Field(None, pattern="^(low|medium|high)$", description="Quality for images/videos")

# Media Upload Progress
class MediaUploadProgress(BaseModel):
    media_id: PyObjectId
    uploaded_bytes: int
    total_bytes: int
    percentage: float
    status: str
    estimated_time_remaining: Optional[int] = None  # seconds

# Bulk Media Operations
class BulkMediaDelete(BaseModel):
    media_ids: List[PyObjectId] = Field(..., min_items=1, max_items=100, description="Media IDs to delete")
    force_delete: bool = Field(False, description="Force delete even if referenced in messages")

class BulkMediaTagUpdate(BaseModel):
    media_ids: List[PyObjectId] = Field(..., min_items=1, max_items=100, description="Media IDs to update")
    tags: List[str] = Field(..., description="Tags to apply")
    action: str = Field("replace", pattern="^(replace|add|remove)$", description="Tag action")

# Media Statistics
class MediaStatsResponse(BaseModel):
    total_files: int
    total_size_bytes: int
    files_by_type: Dict[str, int]
    files_by_status: Dict[str, int]
    storage_usage_by_provider: Dict[str, int]
    largest_files: List[Dict[str, Any]]
    most_downloaded: List[Dict[str, Any]]
    virus_scan_summary: Dict[str, int]

# Media Validation Response
class MediaValidationResponse(BaseModel):
    is_valid: bool
    errors: List[str] = []
    warnings: List[str] = []
    file_info: Dict[str, Any] = {}

# Media Processing Job
class MediaProcessingJob(BaseModel):
    media_id: PyObjectId
    job_type: str  # thumbnail, compression, format_conversion
    status: str  # queued, processing, completed, failed
    progress: float = 0.0
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None 