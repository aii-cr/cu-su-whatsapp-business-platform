"""
Configuration settings for WhatsApp Business Platform Backend.
All environment variables are loaded via Pydantic Settings.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Optional

class Settings(BaseSettings):
    """
    Comprehensive settings class for the WhatsApp Business Platform backend.
    All settings are loaded from environment variables via .env file.
    """
    
    # Application Settings
    APP_NAME: str = "WhatsApp Business Platform Backend"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    API_PREFIX: str = "/api/v1"
    DOMAIN: str = "http://localhost:8000"
    
    # Security Settings
    SECRET_KEY: str = "development-secret-key-change-in-production"  # Default for development
    SESSION_EXPIRE_MINUTES: int = 160  # Session timeout in minutes
    SESSION_INACTIVITY_MINUTES: int = 10  # Session inactivity timeout in minutes
    ALGORITHM: str = "HS256"
    
    # WhatsApp Business API Settings
    WHATSAPP_ACCESS_TOKEN: str 
    WHATSAPP_VERIFY_TOKEN: str 
    WHATSAPP_APP_SECRET: str = "development-app-secret"  # Default for development
    WHATSAPP_BUSINESS_ID: str
    WHATSAPP_PHONE_NUMBER_ID: str
    WHATSAPP_WEBHOOK_URL: str = "https://your-domain.com/api/v1/whatsapp"
    WHATSAPP_API_VERSION: str = "v22.0"
    WHATSAPP_BASE_URL: str = "https://graph.facebook.com"
    
    # WhatsApp Media Settings
    MAX_IMAGE_SIZE_MB: int = 5
    MAX_AUDIO_SIZE_MB: int = 16
    MAX_VIDEO_SIZE_MB: int = 16
    MAX_DOCUMENT_SIZE_MB: int = 100
    SUPPORTED_IMAGE_TYPES: List[str] = ["image/jpeg", "image/png"]
    SUPPORTED_AUDIO_TYPES: List[str] = ["audio/aac", "audio/mp4", "audio/mpeg", "audio/amr", "audio/ogg"]
    SUPPORTED_VIDEO_TYPES: List[str] = ["video/mp4", "video/3gp"]
    SUPPORTED_DOCUMENT_TYPES: List[str] = ["application/pdf", "application/vnd.ms-powerpoint", 
                                          "application/msword", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"]
    
    # MongoDB Settings
    MONGODB_URI: str
    DATABASE_NAME: str
    MONGODB_MIN_POOL_SIZE: int = 10
    MONGODB_MAX_POOL_SIZE: int = 100
    MONGODB_MAX_IDLE_TIME_MS: int = 30000
    
    # Chat & Conversation Settings
    DEFAULT_INACTIVITY_TIMEOUT_HOURS: int = 12
    DEPARTMENT_INACTIVITY_TIMEOUT_HOURS: int = 3
    FOLLOW_UP_INTERVALS_HOURS: List[int] = [1, 3]
    AUTO_CLOSE_ENABLED: bool = True
    SURVEY_ON_CLOSE_ENABLED: bool = True
    MAX_AGENT_TRANSFERS: int = 10
    # Tagging
    MAX_TAGS_PER_CONVERSATION: int = 10
    QUICK_ADD_TAGS_LIMIT: int = 7
    
    # Notification Settings
    ENABLE_PUSH_NOTIFICATIONS: bool = True
    ENABLE_EMAIL_NOTIFICATIONS: bool = True
    NOTIFICATION_BATCH_SIZE: int = 100
    
    # Redis Settings (for caching and WebSocket sessions)
    REDIS_URL: str = "redis://localhost:6379"
    REDIS_PASSWORD: Optional[str] = None
    REDIS_DB: int = 0
    REDIS_MAX_CONNECTIONS: int = 100
    
    # Email Configuration (optional in development)
    SMTP_SERVER: str = "mail.cims.homes"
    SMTP_PORT: int = 465
    SMTP_USE_TLS: bool = True
    SMTP_SENDER_EMAIL: str = "noreply@cims.homes"
    SMTP_SENDER_PASSWORD: str = "development-password"  # Default for development
    SMTP_SENDER_NAME: str = "WhatsApp Business Platform"
    
    # Logging Settings
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"
    LOG_FILE_PATH: str = "logs/app.log"
    LOG_ROTATION_SIZE: str = "10 MB"
    LOG_RETENTION_DAYS: int = 30
    
    # Rate Limiting Settings
    RATE_LIMIT_PER_MINUTE: int = 100
    RATE_LIMIT_BURST: int = 200
    
    # File Upload Settings
    UPLOAD_DIR: str = "uploads"
    TEMP_DIR: str = "temp"
    MAX_UPLOAD_SIZE_MB: int = 100
    
    # Monitoring & Metrics
    ENABLE_METRICS: bool = True
    METRICS_PORT: int = 9090
    HEALTH_CHECK_INTERVAL_SECONDS: int = 30
    
    # Multi-Channel Support
    ENABLE_INSTAGRAM: bool = False
    ENABLE_FACEBOOK_MESSENGER: bool = False
    INSTAGRAM_ACCESS_TOKEN: Optional[str] = None
    FACEBOOK_MESSENGER_ACCESS_TOKEN: Optional[str] = None
    
    # Department & Routing Settings
    DEFAULT_DEPARTMENT: str = "general"
    ENABLE_AUTO_ROUTING: bool = True
    ENABLE_INTELLIGENT_ROUTING: bool = False
    
    # Survey Settings
    SURVEY_TIMEOUT_MINUTES: int = 30
    SURVEY_MAX_RETRIES: int = 3
    DEFAULT_SURVEY_QUESTIONS: List[str] = [
        "How would you rate your experience? (1-5)",
        "Any additional feedback?"
    ]
    
    # Analytics & Reporting
    ENABLE_ANALYTICS: bool = True
    ANALYTICS_RETENTION_DAYS: int = 365
    SENTIMENT_ANALYSIS_ENABLED: bool = False
    
    # WebSocket Settings
    WS_HEARTBEAT_INTERVAL: int = 30
    WS_MAX_CONNECTIONS_PER_USER: int = 5
    WS_MESSAGE_QUEUE_SIZE: int = 1000
    
    # API Documentation
    DOCS_URL: str = "/docs"
    REDOC_URL: str = "/redoc"
    OPENAPI_URL: str = "/openapi.json"
    
    # CORS Settings
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "https://your-frontend-domain.com"]
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: List[str] = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    CORS_ALLOW_HEADERS: List[str] = ["*"]
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"  # Ignore extra fields for flexibility
    )

# Global settings instance
settings = Settings()