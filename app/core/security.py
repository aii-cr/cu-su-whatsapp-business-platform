"""
Legacy security utilities - DEPRECATED.
Please use app.services.auth utilities instead for all new code.
This module is kept for backward compatibility only.
"""

# Import from the new modular auth services
from app.services.auth import *

# Re-export for backward compatibility
__all__ = [
    "get_current_user",
    "get_current_active_user", 
    "get_current_session_token",
    "set_session_cookie",
    "clear_session_cookie",
    "SessionData",
    "get_user_permissions",
    "get_user_roles",
    "check_user_permission",
    "check_user_role",
    "require_permissions",
    "require_roles",
    "hash_password",
    "verify_password",
    "RequireLogin",
    "RequireAdmin",
    "RequireSupervisor", 
    "RequireAgent",
    "RequireUserManagement",
    "RequireConversationAccess",
    "RequireMessageSend",
    "RequireMediaUpload",
    "RequireSystemAdmin",
]

