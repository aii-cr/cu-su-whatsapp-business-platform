"""
Company profile model for the WhatsApp Business Platform.
Manages company information, branding, and platform settings.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from bson import ObjectId
from app.db.models.base import PyObjectId

class CompanyProfile(BaseModel):
    """
    Company profile model for platform configuration and branding.
    """
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    
    # Basic company information
    name: str = Field(..., min_length=1, max_length=200, description="Company name")
    display_name: str = Field(..., min_length=1, max_length=200, description="Public company display name")
    description: Optional[str] = Field(None, max_length=1000, description="Company description")
    
    # Contact information
    email: Optional[str] = Field(None, description="Primary company email")
    phone: Optional[str] = Field(None, description="Primary company phone")
    website: Optional[str] = Field(None, description="Company website URL")
    
    # Address information
    address: Dict[str, Any] = Field(
        default_factory=lambda: {
            "street": None,
            "city": None,
            "state": None,
            "postal_code": None,
            "country": None
        },
        description="Company address information"
    )
    
    # Branding and visual identity
    logo_url: Optional[str] = Field(None, description="Company logo URL")
    profile_photo_url: Optional[str] = Field(None, description="Company profile photo URL")
    brand_colors: Dict[str, str] = Field(
        default_factory=lambda: {
            "primary": "#3B82F6",
            "secondary": "#6B7280",
            "accent": "#10B981",
            "background": "#F9FAFB",
            "text": "#111827"
        },
        description="Brand color scheme"
    )
    
    # Business information
    industry: Optional[str] = Field(None, description="Company industry")
    company_size: Optional[str] = Field(None, description="Company size category")
    founded_year: Optional[int] = Field(None, ge=1800, le=2100, description="Year company was founded")
    registration_number: Optional[str] = Field(None, description="Business registration number")
    tax_id: Optional[str] = Field(None, description="Tax identification number")
    
    # WhatsApp Business settings
    whatsapp_settings: Dict[str, Any] = Field(
        default_factory=lambda: {
            "business_account_id": None,
            "phone_number_id": None,
            "display_phone": None,
            "verified_name": None,
            "about": None,
            "business_profile": {
                "description": None,
                "email": None,
                "address": None,
                "website": []
            },
            "webhook_url": None,
            "webhook_verify_token": None
        },
        description="WhatsApp Business API configuration"
    )
    
    # Platform configuration
    platform_settings: Dict[str, Any] = Field(
        default_factory=lambda: {
            "timezone": "UTC",
            "date_format": "YYYY-MM-DD",
            "time_format": "24h",
            "language": "en",
            "currency": "USD",
            "number_format": "US"
        },
        description="Platform display and formatting settings"
    )
    
    # Business hours and availability
    business_hours: Dict[str, Any] = Field(
        default_factory=lambda: {
            "timezone": "UTC",
            "monday": {"enabled": True, "start": "09:00", "end": "17:00"},
            "tuesday": {"enabled": True, "start": "09:00", "end": "17:00"},
            "wednesday": {"enabled": True, "start": "09:00", "end": "17:00"},
            "thursday": {"enabled": True, "start": "09:00", "end": "17:00"},
            "friday": {"enabled": True, "start": "09:00", "end": "17:00"},
            "saturday": {"enabled": False, "start": "09:00", "end": "17:00"},
            "sunday": {"enabled": False, "start": "09:00", "end": "17:00"},
            "holidays": []
        },
        description="Company business hours configuration"
    )
    
    # Automated messages and responses
    automated_messages: Dict[str, Any] = Field(
        default_factory=lambda: {
            "welcome_message": "Welcome! How can we help you today?",
            "away_message": "We're currently away. We'll get back to you soon!",
            "business_hours_message": "We're currently outside business hours. We'll respond during our next business day.",
            "transfer_message": "You're being transferred to another agent who can better assist you.",
            "survey_message": "How would you rate your experience with us today?",
            "closing_message": "Thank you for contacting us. Have a great day!"
        },
        description="Automated message templates"
    )
    
    # Notification settings
    notification_settings: Dict[str, Any] = Field(
        default_factory=lambda: {
            "email_notifications": True,
            "sms_notifications": False,
            "webhook_notifications": True,
            "real_time_alerts": True,
            "daily_reports": True,
            "weekly_reports": True,
            "monthly_reports": True
        },
        description="Notification preferences"
    )
    
    # Security and compliance settings
    security_settings: Dict[str, Any] = Field(
        default_factory=lambda: {
            "two_factor_auth_required": False,
            "password_policy": {
                "min_length": 8,
                "require_uppercase": True,
                "require_lowercase": True,
                "require_numbers": True,
                "require_special_chars": True
            },
            "session_timeout_minutes": 480,
            "ip_whitelist": [],
            "data_retention_days": 2555  # 7 years
        },
        description="Security and compliance configuration"
    )
    
    # Integration settings
    integrations: Dict[str, Any] = Field(
        default_factory=lambda: {
            "crm": {
                "enabled": False,
                "provider": None,
                "api_key": None,
                "webhook_url": None
            },
            "analytics": {
                "enabled": False,
                "provider": None,
                "tracking_id": None
            },
            "helpdesk": {
                "enabled": False,
                "provider": None,
                "api_key": None
            }
        },
        description="Third-party integration settings"
    )
    
    # Subscription and billing
    subscription: Dict[str, Any] = Field(
        default_factory=lambda: {
            "plan": "basic",
            "status": "active",
            "billing_email": None,
            "billing_address": None,
            "next_billing_date": None,
            "features": []
        },
        description="Subscription and billing information"
    )
    
    # Custom fields and extensions
    custom_fields: Dict[str, Any] = Field(
        default_factory=dict,
        description="Custom company-specific fields"
    )
    
    # Social media and marketing
    social_media: Dict[str, str] = Field(
        default_factory=lambda: {
            "facebook": None,
            "twitter": None,
            "linkedin": None,
            "instagram": None,
            "youtube": None
        },
        description="Social media profile URLs"
    )
    
    # Status and metadata
    is_active: bool = Field(default=True, description="Whether company profile is active")
    is_verified: bool = Field(default=False, description="Whether company is verified")
    verification_date: Optional[datetime] = Field(None, description="Date of verification")
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = Field(None, description="Last admin login")
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {PyObjectId: str}
        json_schema_extra = {
            "example": {
                "name": "Acme Corporation",
                "display_name": "Acme Corp",
                "description": "Leading provider of innovative solutions",
                "email": "contact@acme.com",
                "phone": "+1-555-0123",
                "website": "https://acme.com",
                "industry": "Technology"
            }
        }

class CompanyProfileUpdate(BaseModel):
    """Schema for updating company profile."""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    display_name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    email: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    address: Optional[Dict[str, Any]] = None
    logo_url: Optional[str] = None
    profile_photo_url: Optional[str] = None
    brand_colors: Optional[Dict[str, str]] = None
    industry: Optional[str] = None
    company_size: Optional[str] = None
    whatsapp_settings: Optional[Dict[str, Any]] = None
    platform_settings: Optional[Dict[str, Any]] = None
    business_hours: Optional[Dict[str, Any]] = None
    automated_messages: Optional[Dict[str, Any]] = None
    notification_settings: Optional[Dict[str, Any]] = None
    security_settings: Optional[Dict[str, Any]] = None
    integrations: Optional[Dict[str, Any]] = None
    social_media: Optional[Dict[str, str]] = None
    custom_fields: Optional[Dict[str, Any]] = None
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class CompanyProfileResponse(BaseModel):
    """Schema for company profile responses."""
    id: str = Field(alias="_id")
    name: str
    display_name: str
    description: Optional[str]
    email: Optional[str]
    phone: Optional[str]
    website: Optional[str]
    address: Dict[str, Any]
    logo_url: Optional[str]
    profile_photo_url: Optional[str]
    brand_colors: Dict[str, str]
    industry: Optional[str]
    company_size: Optional[str]
    platform_settings: Dict[str, Any]
    business_hours: Dict[str, Any]
    automated_messages: Dict[str, Any]
    notification_settings: Dict[str, Any]
    social_media: Dict[str, str]
    is_active: bool
    is_verified: bool
    verification_date: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        populate_by_name = True 