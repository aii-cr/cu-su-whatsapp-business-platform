"""Business routes package."""

from fastapi import APIRouter

from .departments import router as departments_router

# Create main business router
router = APIRouter(prefix="/business", tags=["Business"])

# Include all business endpoint routers
router.include_router(departments_router) 