"""Common FastAPI authentication dependencies."""

from fastapi import Depends

from .session_auth import get_current_active_user
from .permissions import require_roles, require_permissions


# Common role-based dependencies
RequireLogin = Depends(get_current_active_user)
RequireAdmin = require_roles(["admin"])
RequireSupervisor = require_roles(["admin", "supervisor"])
RequireAgent = require_roles(["admin", "supervisor", "agent"])

# Common permission-based dependencies
RequireUserManagement = require_permissions(["users.create", "users.update", "users.delete"])
RequireConversationAccess = require_permissions(["conversations.read"])
RequireMessageSend = require_permissions(["messages.create"])
RequireMediaUpload = require_permissions(["media.upload"])
RequireSystemAdmin = require_permissions(["system.admin"]) 