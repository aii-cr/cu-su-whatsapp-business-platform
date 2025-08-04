"""Audit log related request/response schemas."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from app.db.models.base import PyObjectId

# ===== EXISTING GENERAL AUDIT SCHEMAS =====


# Audit Log Creation
class AuditLogCreate(BaseModel):
    action: str = Field(..., description="Action performed")
    category: str = Field(..., description="Action category")
    level: str = Field(
        "info", pattern="^(debug|info|warning|error|critical)$", description="Log level"
    )
    actor_id: Optional[PyObjectId] = Field(None, description="ID of user who performed the action")
    actor_type: str = Field(
        "user", pattern="^(user|system|api|webhook)$", description="Type of actor"
    )
    target_type: Optional[str] = Field(None, description="Type of target resource")
    target_id: Optional[PyObjectId] = Field(None, description="ID of target resource")
    details: Dict[str, Any] = Field(default={}, description="Additional action details")
    ip_address: Optional[str] = Field(None, description="IP address of the actor")
    user_agent: Optional[str] = Field(None, description="User agent string")
    session_id: Optional[str] = Field(None, description="Session identifier")
    request_id: Optional[str] = Field(None, description="Request identifier")


# Audit Log Response
class AuditLogResponse(BaseModel):
    id: PyObjectId = Field(alias="_id")
    action: str
    category: str
    level: str
    actor_id: Optional[PyObjectId] = None
    actor_type: str
    actor_name: Optional[str] = None
    target_type: Optional[str] = None
    target_id: Optional[PyObjectId] = None
    target_name: Optional[str] = None
    details: Dict[str, Any] = {}
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    session_id: Optional[str] = None
    request_id: Optional[str] = None
    timestamp: datetime
    created_at: datetime

    class Config:
        populate_by_name = True
        json_encoders = {PyObjectId: str, datetime: lambda v: v.isoformat()}


# Audit Log List Response
class AuditLogListResponse(BaseModel):
    logs: List[AuditLogResponse]
    total: int
    page: int
    per_page: int
    pages: int


# ===== NEW DOMAIN-SPECIFIC WHATSAPP AUDIT SCHEMAS =====


# WhatsApp Business Audit Log Response
class WhatsAppAuditLogResponse(BaseModel):
    """Response schema for domain-specific WhatsApp Business audit logs."""

    id: PyObjectId = Field(alias="_id")
    conversation_id: Optional[PyObjectId] = None
    customer_phone: Optional[str] = None
    actor_id: Optional[PyObjectId] = None
    actor_name: Optional[str] = None
    department_id: Optional[PyObjectId] = None
    action: str
    payload: Dict[str, Any] = {}
    created_at: datetime
    metadata: Dict[str, Any] = {}

    class Config:
        populate_by_name = True
        json_encoders = {PyObjectId: str, datetime: lambda v: v.isoformat()}


# WhatsApp Business Audit Log List Response
class WhatsAppAuditLogListResponse(BaseModel):
    """Paginated response for WhatsApp Business audit logs."""

    logs: List[WhatsAppAuditLogResponse]
    total: int
    page: int
    per_page: int
    pages: int


# WhatsApp Business Audit Query Parameters
class WhatsAppAuditQueryParams(BaseModel):
    """Query parameters for filtering WhatsApp Business audit logs."""

    page: int = Field(1, ge=1, description="Page number")
    per_page: int = Field(50, ge=1, le=200, description="Items per page")
    action: Optional[str] = Field(None, description="Filter by action type")
    actor_id: Optional[PyObjectId] = Field(None, description="Filter by actor ID")
    actor_name: Optional[str] = Field(None, description="Filter by actor name")
    customer_phone: Optional[str] = Field(None, description="Filter by customer phone")
    conversation_id: Optional[PyObjectId] = Field(None, description="Filter by conversation ID")
    department_id: Optional[PyObjectId] = Field(None, description="Filter by department ID")
    from_date: Optional[datetime] = Field(None, description="Filter logs from this date")
    to_date: Optional[datetime] = Field(None, description="Filter logs to this date")
    correlation_id: Optional[str] = Field(None, description="Filter by correlation ID")
    sort_by: str = Field("created_at", description="Sort field")
    sort_order: str = Field("desc", pattern="^(asc|desc)$", description="Sort order")


# ===== ORIGINAL GENERAL AUDIT SCHEMAS (CONTINUED) =====


# Audit Log Query Parameters
class AuditLogQueryParams(BaseModel):
    page: int = Field(1, ge=1, description="Page number")
    per_page: int = Field(50, ge=1, le=200, description="Items per page")
    action: Optional[str] = Field(None, description="Filter by action")
    category: Optional[str] = Field(None, description="Filter by category")
    level: Optional[str] = Field(None, description="Filter by log level")
    actor_id: Optional[PyObjectId] = Field(None, description="Filter by actor ID")
    actor_type: Optional[str] = Field(None, description="Filter by actor type")
    target_type: Optional[str] = Field(None, description="Filter by target type")
    target_id: Optional[PyObjectId] = Field(None, description="Filter by target ID")
    from_date: Optional[datetime] = Field(None, description="Filter logs from this date")
    to_date: Optional[datetime] = Field(None, description="Filter logs to this date")
    ip_address: Optional[str] = Field(None, description="Filter by IP address")
    session_id: Optional[str] = Field(None, description="Filter by session ID")
    request_id: Optional[str] = Field(None, description="Filter by request ID")
    search: Optional[str] = Field(None, description="Search in action or details")
    sort_by: str = Field("timestamp", description="Sort field")
    sort_order: str = Field("desc", pattern="^(asc|desc)$", description="Sort order")


# Audit Log Statistics
class AuditLogStatsResponse(BaseModel):
    total_logs: int
    logs_by_category: Dict[str, int]
    logs_by_level: Dict[str, int]
    logs_by_actor_type: Dict[str, int]
    most_active_actors: List[Dict[str, Any]]
    activity_by_hour: List[Dict[str, Any]]
    top_actions: List[Dict[str, Any]]


# Audit Log Export Request
class AuditLogExportRequest(BaseModel):
    from_date: Optional[datetime] = Field(None, description="Export logs from this date")
    to_date: Optional[datetime] = Field(None, description="Export logs to this date")
    categories: Optional[List[str]] = Field(None, description="Export specific categories")
    levels: Optional[List[str]] = Field(None, description="Export specific log levels")
    actor_ids: Optional[List[PyObjectId]] = Field(
        None, description="Export logs for specific actors"
    )
    format: str = Field("csv", pattern="^(csv|json|xlsx)$", description="Export format")
    include_details: bool = Field(True, description="Include details in export")
    email_to: Optional[str] = Field(None, description="Email address to send export")


# Security Event
class SecurityEvent(BaseModel):
    event_type: str = Field(..., description="Type of security event")
    severity: str = Field(..., pattern="^(low|medium|high|critical)$", description="Event severity")
    actor_id: Optional[PyObjectId] = Field(None, description="Actor involved in the event")
    target_id: Optional[PyObjectId] = Field(None, description="Target of the event")
    details: Dict[str, Any] = Field(..., description="Event details")
    ip_address: Optional[str] = Field(None, description="IP address")
    user_agent: Optional[str] = Field(None, description="User agent")
    mitigated: bool = Field(False, description="Whether the event was mitigated")
    mitigation_details: Optional[str] = Field(None, description="Mitigation details")


# Compliance Report
class ComplianceReport(BaseModel):
    report_id: str
    report_type: str  # gdpr, ccpa, audit_trail, security
    period_start: datetime
    period_end: datetime
    generated_at: datetime
    generated_by: PyObjectId
    status: str  # generating, completed, failed
    summary: Dict[str, Any] = {}
    download_url: Optional[str] = None
    expires_at: Optional[datetime] = None


# System Activity Summary
class SystemActivitySummary(BaseModel):
    date: datetime
    total_actions: int
    unique_actors: int
    failed_actions: int
    security_events: int
    critical_events: int
    top_actions: List[Dict[str, str]]
    peak_activity_hour: int


# Data Retention Policy
class DataRetentionPolicy(BaseModel):
    category: str
    retention_days: int
    auto_delete: bool
    archive_before_delete: bool
    compliance_requirement: Optional[str] = None
    last_cleanup: Optional[datetime] = None
    next_cleanup: Optional[datetime] = None


# Audit Configuration
class AuditConfiguration(BaseModel):
    enabled_categories: List[str] = Field(default=[], description="Enabled audit categories")
    log_levels: List[str] = Field(
        default=["info", "warning", "error", "critical"], description="Enabled log levels"
    )
    retention_days: int = Field(365, ge=30, description="Log retention period")
    auto_archive: bool = Field(True, description="Enable automatic archiving")
    real_time_alerts: bool = Field(True, description="Enable real-time security alerts")
    export_enabled: bool = Field(True, description="Enable log export")
    anonymize_pii: bool = Field(True, description="Anonymize PII in logs")
    encryption_enabled: bool = Field(True, description="Enable log encryption")
