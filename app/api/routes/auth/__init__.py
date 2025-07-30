"""Authentication and authorization endpoints."""

from fastapi import APIRouter

from .users import router as users_router
from .roles import router as roles_router
from .permissions import router as permissions_router

router = APIRouter(prefix="/auth", tags=["authentication"])

router.include_router(users_router)
router.include_router(roles_router)
router.include_router(permissions_router) 