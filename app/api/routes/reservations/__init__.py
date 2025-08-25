"""Reservations routes package for installation scheduling."""

from fastapi import APIRouter

from .create_collection import router as create_collection_router
from .get_available_slots import router as get_available_slots_router
from .book_reservation import router as book_reservation_router

# Create main reservations router
router = APIRouter(prefix="/reservations", tags=["reservations"])

# Include all reservation endpoint routers
router.include_router(create_collection_router)
router.include_router(get_available_slots_router)
router.include_router(book_reservation_router)
