"""WhatsApp chat messages routes package."""

from fastapi import APIRouter

from .send_message import router as send_message_router
from .send_template import router as send_template_router
from .send_media import router as send_media_router
from .get_messages import router as get_messages_router
from .get_templates import router as get_templates_router
from .send_bulk import router as send_bulk_router

# Create main messages router
router = APIRouter(prefix="/messages", tags=["messages"])

# Include all message endpoint routers
router.include_router(send_message_router)
router.include_router(send_template_router)
router.include_router(send_media_router)
router.include_router(get_messages_router)
router.include_router(get_templates_router)
router.include_router(send_bulk_router) 