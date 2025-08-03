"""User management routes package."""

from fastapi import APIRouter

from .register_user import router as register_user_router
from .login_user import router as login_user_router
from .logout_user import router as logout_user_router
from .user_profile import router as user_profile_router
from .list_users import router as list_users_router
from .get_user import router as get_user_router
from .manage_users import router as manage_users_router
from .user_stats import router as user_stats_router

# Create main users router
router = APIRouter(prefix="/users", tags=["Users"])

# Include all user endpoint routers
router.include_router(register_user_router)
router.include_router(login_user_router)
router.include_router(logout_user_router)
router.include_router(user_profile_router)
router.include_router(list_users_router)
router.include_router(get_user_router)
router.include_router(manage_users_router)
router.include_router(user_stats_router) 