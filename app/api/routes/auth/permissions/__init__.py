"""Permission management endpoints."""

from fastapi import APIRouter

from .create_permission import router as create_permission_router
from .list_permissions import router as list_permissions_router
from .get_permission import router as get_permission_router
from .update_permission import router as update_permission_router
from .delete_permission import router as delete_permission_router

router = APIRouter(prefix="/permissions", tags=["permissions"])

router.include_router(create_permission_router)
router.include_router(list_permissions_router)
router.include_router(get_permission_router)
router.include_router(update_permission_router)
router.include_router(delete_permission_router) 