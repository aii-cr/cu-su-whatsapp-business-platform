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
    "get_current_user_token",
    "get_user_permissions",
    "get_user_roles",
    "check_user_permission",
    "check_user_role",
    "require_permissions",
    "require_roles",
    "create_access_token",
    "create_refresh_token", 
    "verify_token",
    "TokenData",
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

