"""Authentication services package."""

from .utils import *
from .user_service import user_service
from .role_service import role_service
from .permission_service import permission_service

__all__ = [
    # Re-export all auth utilities (session-based)
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
    
    # Service instances
    "user_service",
    "role_service", 
    "permission_service"
] 