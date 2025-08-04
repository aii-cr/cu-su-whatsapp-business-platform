"""Authentication utilities package.

This package provides modular authentication utilities including:
- User authentication and authorization
- Permission and role checking
- Session-based authentication
- Password utilities
- FastAPI dependencies
"""

from .session_auth import (
    get_current_user, get_current_active_user, get_current_session_token,
    set_session_cookie, clear_session_cookie, SessionData,
    create_session_token, verify_session_token
)
from .permissions import (
    get_user_permissions, get_user_roles, check_user_permission, 
    check_user_role, require_permissions, require_roles
)
from .password_utils import hash_password, verify_password
from .dependencies import (
    RequireLogin, RequireAdmin, RequireSupervisor, RequireAgent,
    RequireUserManagement, RequireConversationAccess, RequireMessageSend,
    RequireMediaUpload, RequireSystemAdmin
)

__all__ = [
    # User authentication (session-based)
    "get_current_user",
    "get_current_active_user", 
    "get_current_session_token",
    "set_session_cookie",
    "clear_session_cookie",
    "SessionData",
    "create_session_token",
    "verify_session_token",
    
    # Permissions and roles
    "get_user_permissions",
    "get_user_roles",
    "check_user_permission",
    "check_user_role",
    "require_permissions",
    "require_roles",
    
    # Password utilities
    "hash_password",
    "verify_password",
    
    # Common dependencies
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