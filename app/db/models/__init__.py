"""
Database models package with organized submodules.

Models are organized into logical categories:
- auth: Authentication and authorization models
- chat: Messaging and conversation models  
- business: Organization and company models
- system: System and compliance models
"""

# Authentication models
from .auth import User, Role, Permission

# Chat and messaging models
from .chat import Conversation, Message, Media, Tag, Note

# Business and organizational models
from .business import Department, CompanyProfile

# System and compliance models
from .system import AuditLog

__all__ = [
    # Auth models
    "User", "Role", "Permission",
    
    # Chat models
    "Conversation", "Message", "Media", "Tag", "Note",
    
    # Business models
    "Department", "CompanyProfile",
    
    # System models
    "AuditLog"
]
