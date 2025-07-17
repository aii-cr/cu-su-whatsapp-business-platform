"""Company profile related request/response schemas."""

from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime
from app.db.models.base import PyObjectId

# Company Profile Update
class CompanyProfileUpdate(BaseModel):
    company_name: Optional[str] = Field(None, min_length=1, max_length=200, description="Company name")
    business_description: Optional[str] = Field(None, max_length=1000, description="Business description")
    industry: Optional[str] = Field(None, description="Industry category")
    website: Optional[str] = Field(None, description="Company website")
    primary_email: Optional[EmailStr] = Field(None, description="Primary contact email")
    support_email: Optional[EmailStr] = Field(None, description="Support email")
    primary_phone: Optional[str] = Field(None, description="Primary phone number")
    support_phone: Optional[str] = Field(None, description="Support phone number")
    address: Optional[Dict[str, str]] = Field(None, description="Company address")
    timezone: Optional[str] = Field(None, description="Primary timezone")
    language: Optional[str] = Field(None, description="Primary language")
    currency: Optional[str] = Field(None, description="Primary currency")
    branding: Optional[Dict[str, Any]] = Field(None, description="Branding configuration")
    business_hours: Optional[Dict[str, Any]] = Field(None, description="Default business hours")
    features: Optional[Dict[str, bool]] = Field(None, description="Enabled features")
    integrations: Optional[Dict[str, Any]] = Field(None, description="Integration settings")
    compliance: Optional[Dict[str, Any]] = Field(None, description="Compliance settings")
    notification_preferences: Optional[Dict[str, Any]] = Field(None, description="Notification preferences")

# Company Profile Response
class CompanyProfileResponse(BaseModel):
    id: PyObjectId = Field(alias="_id")
    company_name: str
    business_description: Optional[str] = None
    industry: Optional[str] = None
    website: Optional[str] = None
    primary_email: Optional[str] = None
    support_email: Optional[str] = None
    primary_phone: Optional[str] = None
    support_phone: Optional[str] = None
    address: Dict[str, str] = {}
    timezone: str
    language: str
    currency: str
    branding: Dict[str, Any] = {}
    business_hours: Dict[str, Any] = {}
    features: Dict[str, bool] = {}
    integrations: Dict[str, Any] = {}
    compliance: Dict[str, Any] = {}
    notification_preferences: Dict[str, Any] = {}
    created_at: datetime
    updated_at: datetime
    subscription_status: str
    plan_type: str
    usage_limits: Dict[str, Any] = {}

    class Config:
        populate_by_name = True
        json_encoders = {
            PyObjectId: str,
            datetime: lambda v: v.isoformat()
        }

# Branding Configuration
class BrandingConfig(BaseModel):
    logo_url: Optional[str] = Field(None, description="Company logo URL")
    primary_color: str = Field("#007bff", pattern="^#[0-9A-Fa-f]{6}$", description="Primary brand color")
    secondary_color: str = Field("#6c757d", pattern="^#[0-9A-Fa-f]{6}$", description="Secondary brand color")
    font_family: str = Field("Inter", description="Primary font family")
    custom_css: Optional[str] = Field(None, description="Custom CSS styles")
    favicon_url: Optional[str] = Field(None, description="Favicon URL")
    email_header_logo: Optional[str] = Field(None, description="Email header logo URL")
    watermark_enabled: bool = Field(True, description="Show branding watermark")

# Feature Configuration
class FeatureConfig(BaseModel):
    whatsapp_enabled: bool = Field(True, description="WhatsApp integration enabled")
    instagram_enabled: bool = Field(False, description="Instagram integration enabled")
    facebook_messenger_enabled: bool = Field(False, description="Facebook Messenger enabled")
    live_chat_enabled: bool = Field(True, description="Live chat widget enabled")
    chatbot_enabled: bool = Field(False, description="Chatbot enabled")
    file_sharing_enabled: bool = Field(True, description="File sharing enabled")
    screen_sharing_enabled: bool = Field(False, description="Screen sharing enabled")
    voice_notes_enabled: bool = Field(True, description="Voice notes enabled")
    video_calls_enabled: bool = Field(False, description="Video calls enabled")
    survey_enabled: bool = Field(True, description="Customer surveys enabled")
    analytics_enabled: bool = Field(True, description="Analytics and reporting enabled")
    api_access_enabled: bool = Field(True, description="API access enabled")

# Integration Settings
class IntegrationSettings(BaseModel):
    crm_integration: Dict[str, Any] = Field(default={}, description="CRM integration settings")
    helpdesk_integration: Dict[str, Any] = Field(default={}, description="Helpdesk integration settings")
    analytics_integration: Dict[str, Any] = Field(default={}, description="Analytics integration settings")
    payment_integration: Dict[str, Any] = Field(default={}, description="Payment integration settings")
    sms_integration: Dict[str, Any] = Field(default={}, description="SMS integration settings")
    email_integration: Dict[str, Any] = Field(default={}, description="Email integration settings")
    webhook_settings: Dict[str, Any] = Field(default={}, description="Webhook configuration")

# Compliance Settings
class ComplianceSettings(BaseModel):
    data_retention_days: int = Field(365, ge=30, le=2555, description="Data retention period in days")
    gdpr_enabled: bool = Field(True, description="GDPR compliance enabled")
    ccpa_enabled: bool = Field(False, description="CCPA compliance enabled")
    audit_logging_enabled: bool = Field(True, description="Audit logging enabled")
    encryption_enabled: bool = Field(True, description="Data encryption enabled")
    backup_enabled: bool = Field(True, description="Automated backups enabled")
    export_enabled: bool = Field(True, description="Data export enabled")
    anonymization_enabled: bool = Field(True, description="Data anonymization enabled")
    consent_tracking_enabled: bool = Field(True, description="Consent tracking enabled")

# Notification Preferences
class NotificationPreferences(BaseModel):
    email_notifications: Dict[str, bool] = Field(
        default={
            "new_conversation": True,
            "message_received": False,
            "agent_assigned": True,
            "sla_breach": True,
            "system_alerts": True
        },
        description="Email notification settings"
    )
    push_notifications: Dict[str, bool] = Field(
        default={
            "new_conversation": True,
            "message_received": True,
            "agent_assigned": True,
            "mentions": True
        },
        description="Push notification settings"
    )
    sms_notifications: Dict[str, bool] = Field(
        default={
            "critical_alerts": True,
            "sla_breach": False,
            "system_down": True
        },
        description="SMS notification settings"
    )
    webhook_notifications: Dict[str, bool] = Field(
        default={
            "conversation_events": True,
            "message_events": True,
            "agent_events": True,
            "system_events": False
        },
        description="Webhook notification settings"
    )

# Company Statistics
class CompanyStatsResponse(BaseModel):
    total_users: int
    total_conversations: int
    total_messages: int
    active_agents: int
    departments_count: int
    storage_used_mb: float
    api_calls_today: int
    subscription_days_remaining: int
    feature_usage: Dict[str, Any]

# Usage Limits
class UsageLimits(BaseModel):
    max_agents: int = Field(50, description="Maximum number of agents")
    max_conversations_per_month: int = Field(10000, description="Maximum conversations per month")
    max_messages_per_month: int = Field(100000, description="Maximum messages per month")
    max_storage_mb: int = Field(10240, description="Maximum storage in MB")
    max_api_calls_per_day: int = Field(10000, description="Maximum API calls per day")
    max_departments: int = Field(20, description="Maximum number of departments")
    max_integrations: int = Field(10, description="Maximum number of integrations")

# Subscription Information
class SubscriptionInfo(BaseModel):
    plan_type: str
    status: str  # active, expired, suspended, trial
    start_date: datetime
    end_date: datetime
    renewal_date: Optional[datetime] = None
    billing_cycle: str  # monthly, yearly
    amount: float
    currency: str
    features_included: List[str]
    usage_limits: UsageLimits
    auto_renew: bool

# Company Backup
class CompanyBackup(BaseModel):
    backup_id: str
    created_at: datetime
    size_mb: float
    status: str  # creating, completed, failed
    includes: List[str]  # conversations, users, settings, media
    download_url: Optional[str] = None
    expires_at: Optional[datetime] = None 