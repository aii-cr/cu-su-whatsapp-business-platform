"""Logging configuration for the WhatsApp Business Platform backend."""

import logging
import sys
import json
from datetime import datetime
from typing import Dict, Any
from pathlib import Path

from app.core.config import settings

class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields
        for key, value in record.__dict__.items():
            if key not in {
                'name', 'msg', 'args', 'levelname', 'levelno', 'pathname', 
                'filename', 'module', 'exc_info', 'exc_text', 'stack_info',
                'lineno', 'funcName', 'created', 'msecs', 'relativeCreated',
                'thread', 'threadName', 'processName', 'process', 'getMessage'
            }:
                log_entry[key] = value
        
        return json.dumps(log_entry, default=str)

def setup_logging():
    """Configure application logging."""
    
    # Create logs directory if it doesn't exist
    log_dir = Path(settings.LOG_FILE_PATH).parent
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper()))
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Create formatters
    if settings.LOG_FORMAT.lower() == "json":
        formatter = JSONFormatter()
    else:
        formatter = logging.Formatter(
            fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO)
    root_logger.addHandler(console_handler)
    
    # File handler with rotation
    try:
        from logging.handlers import RotatingFileHandler
        file_handler = RotatingFileHandler(
            settings.LOG_FILE_PATH,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(getattr(logging, settings.LOG_LEVEL.upper()))
        root_logger.addHandler(file_handler)
    except Exception as e:
        print(f"Failed to setup file logging: {e}")
    
    # Suppress noisy loggers
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)

def get_logger(name: str) -> logging.Logger:
    """Get a logger instance."""
    return logging.getLogger(name)

# Create application logger
logger = get_logger("whatsapp_platform")

# Structured logging helpers
def log_api_request(method: str, path: str, user_id: str = None, **kwargs):
    """Log API request."""
    logger.info(
        "API request",
        extra={
            "event_type": "api_request",
            "method": method,
            "path": path,
            "user_id": user_id,
            **kwargs
        }
    )

def log_api_response(method: str, path: str, status_code: int, response_time: float, **kwargs):
    """Log API response."""
    logger.info(
        "API response",
        extra={
            "event_type": "api_response",
            "method": method,
            "path": path,
            "status_code": status_code,
            "response_time_ms": response_time * 1000,
            **kwargs
        }
    )

def log_webhook_event(event_type: str, webhook_id: str, **kwargs):
    """Log webhook event."""
    logger.info(
        f"Webhook {event_type}",
        extra={
            "event_type": "webhook",
            "webhook_event": event_type,
            "webhook_id": webhook_id,
            **kwargs
        }
    )

def log_conversation_event(event_type: str, conversation_id: str, **kwargs):
    """Log conversation event."""
    logger.info(
        f"Conversation {event_type}",
        extra={
            "event_type": "conversation",
            "conversation_event": event_type,
            "conversation_id": conversation_id,
            **kwargs
        }
    )

def log_security_event(event_type: str, severity: str = "medium", **kwargs):
    """Log security event."""
    logger.warning(
        f"Security event: {event_type}",
        extra={
            "event_type": "security",
            "security_event": event_type,
            "severity": severity,
            **kwargs
        }
    )

def log_error(error: Exception, context: Dict[str, Any] = None):
    """Log error with context."""
    logger.error(
        f"Error: {str(error)}",
        extra={
            "event_type": "error",
            "error_type": type(error).__name__,
            "context": context or {},
        },
        exc_info=True
    )

# Initialize logging on import
setup_logging()
