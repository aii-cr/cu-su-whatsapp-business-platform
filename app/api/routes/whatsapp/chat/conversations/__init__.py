"""WhatsApp chat conversations routes package."""

from fastapi import APIRouter

from .create_conversation import router as create_conversation_router
from .start_conversation import router as start_conversation_router
from .list_conversations import router as list_conversations_router
from .get_conversation import router as get_conversation_router
from .get_conversation_with_messages import router as get_conversation_with_messages_router
from .update_conversation import router as update_conversation_router
from .delete_conversation import router as delete_conversation_router
from .get_stats import router as get_stats_router
from .close_conversation import router as close_conversation_router
from .transfer_conversation import router as transfer_conversation_router

# Create main conversations router
router = APIRouter(prefix="/conversations", tags=["Conversations"])

# Include all conversation endpoint routers
router.include_router(create_conversation_router)
router.include_router(start_conversation_router)
router.include_router(list_conversations_router)
router.include_router(get_conversation_router)
router.include_router(get_conversation_with_messages_router)
router.include_router(update_conversation_router)
router.include_router(delete_conversation_router)
router.include_router(get_stats_router)
router.include_router(close_conversation_router)
router.include_router(transfer_conversation_router) 