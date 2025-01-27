from app.db.chat_platform_db import mongo
from bson.objectid import ObjectId


class ChatPlatformService:
    @staticmethod
    async def create_user(user: dict):
        """
        Create a new user document in the users collection.
        """
        await mongo.db.users.insert_one(user)

    @staticmethod
    async def get_user(user_id: str):
        """
        Retrieve a user by ID.
        """
        return await mongo.db.users.find_one({"_id": ObjectId(user_id)})

    @staticmethod
    async def create_message(message: dict):
        """
        Add a new message to the messages collection.
        """
        await mongo.db.messages.insert_one(message)

    @staticmethod
    async def get_conversation(conversation_id: str):
        """
        Retrieve a conversation by ID.
        """
        return await mongo.db.conversations.find_one({"_id": ObjectId(conversation_id)})

    @staticmethod
    async def update_conversation(conversation_id: str, updates: dict):
        """
        Update conversation details.
        """
        await mongo.db.conversations.update_one(
            {"_id": ObjectId(conversation_id)}, {"$set": updates}
        )
