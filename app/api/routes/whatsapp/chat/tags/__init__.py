"""WhatsApp chat tags routes package."""

from fastapi import APIRouter

from .list_tags import router as list_tags_router
from .create_tag import router as create_tag_router
from .get_tag import router as get_tag_router
from .update_tag import router as update_tag_router
from .delete_tag import router as delete_tag_router
from .suggest_tags import router as suggest_tags_router

# Create main tags router
router = APIRouter(prefix="/tags", tags=["Tags"])

# Include all tag endpoint routers
router.include_router(list_tags_router)
router.include_router(create_tag_router)
router.include_router(get_tag_router)
router.include_router(update_tag_router)
router.include_router(delete_tag_router)
router.include_router(suggest_tags_router)
