from motor.motor_asyncio import AsyncIOMotorClient
from app.config import settings

class MongoDBClient:
    _client: AsyncIOMotorClient = None

    @classmethod
    def get_client(cls):
        if cls._client is None:
            cls._client = AsyncIOMotorClient(settings.MONGO_URI)
            print("Connected to MongoDB")
        return cls._client

    @classmethod
    def close_client(cls):
        if cls._client:
            cls._client.close()
            print("MongoDB connection closed")
            cls._client = None
