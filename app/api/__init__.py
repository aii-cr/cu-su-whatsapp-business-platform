"""
API package for WhatsApp Business Platform Backend.
Exports the main API router and common dependencies.
"""

from .routes import api_router

__all__ = ["api_router"]
