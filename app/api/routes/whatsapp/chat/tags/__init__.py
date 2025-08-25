"""Enhanced tags routes package."""

from fastapi import APIRouter

from .create_tag import router as create_tag_router
from .list_tags import router as list_tags_router
from .get_tag import router as get_tag_router
from .update_tag import router as update_tag_router
from .delete_tag import router as delete_tag_router
from .search_tags import router as search_tags_router
from .suggest_tags import router as suggest_tags_router
from .get_quick_add_tags import router as get_quick_add_tags_router
from .get_settings import router as get_settings_router

# Create main tags router
router = APIRouter(prefix="/tags", tags=["Tags"])

# Include tag endpoint routers - ORDER MATTERS!
# Specific paths MUST come before parameterized paths
router.include_router(search_tags_router)      # /search
router.include_router(suggest_tags_router)     # /suggest  
router.include_router(get_quick_add_tags_router)  # /quick-add
router.include_router(get_settings_router)     # /settings
router.include_router(list_tags_router)        # /
router.include_router(create_tag_router)       # /
router.include_router(get_tag_router)          # /{tag_id} - MUST be after specific paths
router.include_router(update_tag_router)       # /{tag_id}
router.include_router(delete_tag_router)       # /{tag_id}