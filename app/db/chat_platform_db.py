from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings
from app.core.logger import logger


class MongoDB:
    
    def __init__(self):
        self.client = None
        self.db = None

    async def connect(self):
        """
        Connect to MongoDB and initialize the database.
        """
        self.client = AsyncIOMotorClient(settings.MONGODB_URI)
        self.db = self.client[settings.DATABASE_NAME]
        logger.info(f"Connected to MongoDB database: {settings.DATABASE_NAME}")

    async def disconnect(self):
        """
        Disconnect from MongoDB.
        """
        self.client.close()
        logger.info("Disconnected from MongoDB")


# Singleton instance of MongoDB
mongo = MongoDB()
