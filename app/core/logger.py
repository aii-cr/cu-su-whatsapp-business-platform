"""Logging configuration for the WhatsApp Business Platform backend."""

import logging
import sys
import json
from datetime import datetime, timezone
from typing import Dict, Any
from pathlib import Path

from app.core.config import settings

class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
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

class ConsoleFormatter(logging.Formatter):
    """Human-friendly formatter for console output with colors and line breaks."""
    
    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
        'RESET': '\033[0m',     # Reset
        'BOLD': '\033[1m',      # Bold
        'DIM': '\033[2m',       # Dim
    }
    
    def format(self, record: logging.LogRecord) -> str:
        # Get color for log level
        level_color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        reset_color = self.COLORS['RESET']
        
        # Format timestamp
        timestamp = datetime.fromtimestamp(record.created, tz=timezone.utc).strftime('%H:%M:%S')
        
        # Format the main message
        formatted = f"{self.COLORS['DIM']}{timestamp}{reset_color} "
        formatted += f"{level_color}{record.levelname:8}{reset_color} "
        formatted += f"{self.COLORS['BOLD']}{record.module}.{record.funcName}:{record.lineno}{reset_color} "
        formatted += f"{record.getMessage()}"
        
        # Add extra fields if present (API requests, responses, etc.)
        extra_fields = []
        for key, value in record.__dict__.items():
            if key not in {
                'name', 'msg', 'args', 'levelname', 'levelno', 'pathname', 
                'filename', 'module', 'exc_info', 'exc_text', 'stack_info',
                'lineno', 'funcName', 'created', 'msecs', 'relativeCreated',
                'thread', 'threadName', 'processName', 'process', 'getMessage'
            }:
                extra_fields.append(f"{key}={value}")
        
        if extra_fields:
            formatted += f"\n{self.COLORS['DIM']}  └─ {', '.join(extra_fields)}{reset_color}"
        
        # Add exception info if present
        if record.exc_info:
            formatted += f"\n{self.COLORS['ERROR']}{self.formatException(record.exc_info)}{reset_color}"
        
        return formatted

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
    
    # Console handler with human-friendly formatter
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(ConsoleFormatter())
    console_handler.setLevel(logging.INFO)
    root_logger.addHandler(console_handler)
    
    # File handler with JSON formatter for structured logging
    try:
        from logging.handlers import RotatingFileHandler
        file_handler = RotatingFileHandler(
            settings.LOG_FILE_PATH,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5
        )
        file_handler.setFormatter(JSONFormatter())
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
