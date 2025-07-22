"""Authentication utilities package.

This package provides modular authentication utilities including:
- User authentication and authorization
- Permission and role checking
- JWT token management
- Password utilities
- FastAPI dependencies
"""

from .user_auth import get_current_user, get_current_active_user, get_current_user_token
from .permissions import (
    get_user_permissions, get_user_roles, check_user_permission, 
    check_user_role, require_permissions, require_roles
)
from .tokens import (
    create_access_token, create_refresh_token, verify_token, TokenData
)
from .password_utils import hash_password, verify_password
from .dependencies import (
    RequireLogin, RequireAdmin, RequireSupervisor, RequireAgent,
    RequireUserManagement, RequireConversationAccess, RequireMessageSend,
    RequireMediaUpload, RequireSystemAdmin
)

__all__ = [
    # User authentication
    "get_current_user",
    "get_current_active_user", 
    "get_current_user_token",
    
    # Permissions and roles
    "get_user_permissions",
    "get_user_roles",
    "check_user_permission",
    "check_user_role",
    "require_permissions",
    "require_roles",
    
    # Tokens
    "create_access_token",
    "create_refresh_token", 
    "verify_token",
    "TokenData",
    
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