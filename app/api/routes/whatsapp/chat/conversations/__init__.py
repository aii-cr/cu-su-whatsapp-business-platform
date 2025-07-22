"""WhatsApp chat conversations routes package."""

from fastapi import APIRouter

from .create_conversation import router as create_conversation_router
from .list_conversations import router as list_conversations_router
from .get_conversation import router as get_conversation_router
from .update_conversation import router as update_conversation_router
from .get_stats import router as get_stats_router

# Create main conversations router
router = APIRouter(prefix="/conversations", tags=["Conversations"])

# Include all conversation endpoint routers
router.include_router(create_conversation_router)
router.include_router(list_conversations_router)
router.include_router(get_conversation_router)
router.include_router(update_conversation_router)
router.include_router(get_stats_router) 