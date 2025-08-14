"""Simple conversation tags routes package."""

from .assign_tags import router as assign_tags_router
from .unassign_tags import router as unassign_tags_router  
from .get_conversation_tags import router as get_conversation_tags_router

__all__ = [
    "assign_tags_router",
    "unassign_tags_router", 
    "get_conversation_tags_router"
]