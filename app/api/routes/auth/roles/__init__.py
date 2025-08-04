"""Role management routes package."""

from fastapi import APIRouter

from .create_role import router as create_role_router
from .list_roles import router as list_roles_router
from .get_role import router as get_role_router
from .update_role import router as update_role_router
from .delete_role import router as delete_role_router

# Create main roles router
router = APIRouter(prefix="/roles", tags=["Roles"])

# Include all role endpoint routers
router.include_router(create_role_router)
router.include_router(list_roles_router)
router.include_router(get_role_router)
router.include_router(update_role_router)
router.include_router(delete_role_router) 