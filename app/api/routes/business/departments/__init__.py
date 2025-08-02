"""Department routes package."""

from fastapi import APIRouter

from .create_department import router as create_department_router
from .get_department import router as get_department_router
from .list_departments import router as list_departments_router
from .update_department import router as update_department_router
from .delete_department import router as delete_department_router
from .add_user_to_department import router as add_user_to_department_router
from .remove_user_from_department import router as remove_user_from_department_router

# Create main departments router
router = APIRouter(prefix="/departments", tags=["Departments"])

# Include all department endpoint routers
router.include_router(create_department_router)
router.include_router(list_departments_router)
router.include_router(get_department_router)
router.include_router(update_department_router)
router.include_router(delete_department_router)
router.include_router(add_user_to_department_router)
router.include_router(remove_user_from_department_router) 