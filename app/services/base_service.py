"""Base service class for all services."""

from typing import Optional
from app.db.client import database
from app.core.logger import logger


class BaseService:
    """Base service class with common functionality."""
    
    def __init__(self):
        # Initialize db as None, but set it if database is already connected
        self.db = None
        if hasattr(database, 'is_connected') and database.is_connected:
            self.db = database.db
    
    async def _ensure_db_connection(self):
        """Ensure database connection is established."""
        if self.db is None:
            if not database.is_connected:
                await database.connect()
            self.db = database.db
    
    async def _get_db(self):
        """Get database instance with connection guarantee."""
        await self._ensure_db_connection()
        return self.db
    
    async def health_check(self) -> dict:
        """Service health check."""
        try:
            await self._ensure_db_connection()
            return {"status": "healthy", "service": self.__class__.__name__}
        except Exception as e:
            logger.error(f"Service health check failed: {str(e)}")
            return {"status": "unhealthy", "service": self.__class__.__name__, "error": str(e)}