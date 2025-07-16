from fastapi import APIRouter
from .whatsapp import webhook, conversation, send_test_message, test_db

router = APIRouter()

router.include_router(webhook.router)
router.include_router(conversation.router)
router.include_router(send_test_message.router)
router.include_router(test_db.router)

