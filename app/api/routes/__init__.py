from fastapi import APIRouter
from .whatsapp import router as whatsapp_router

router = APIRouter()
router.include_router(whatsapp_router)
