from datetime import datetime
from fastapi import HTTPException
from app.db.chat_platform_db import mongo
from bson.objectid import ObjectId
from app.core.logger import logger

class ChatPlatformService:
    @staticmethod
    async def create_conversation(conversation_id: str, participants: list):
        """
        Create a new conversation if it doesn't exist.
        """
        existing_conversation = await mongo.db.conversations.find_one({"conversation_id": conversation_id})
        if not existing_conversation:
            conversation_data = {
                "conversation_id": conversation_id,
                "participants": participants,
                "last_message": None,
                "created_at": datetime.now(),
                "updated_at": datetime.now()
            }
            await mongo.db.conversations.insert_one(conversation_data)
            logger.info(f"Created new conversation: {conversation_id}")

    @staticmethod
    async def create_message(message: dict):
        """
        Save a message and ensure conversation exists.
        """
        try:
            # Convert WhatsApp timestamp (Unix timestamp string) to datetime
            if "timestamp" in message and isinstance(message["timestamp"], str):
                message["timestamp"] = datetime.fromtimestamp(int(message["timestamp"]))

            # Ensure the conversation exists before adding the message
            await ChatPlatformService.create_conversation(
                message["conversation_id"], 
                [message["sender_id"], message["receiver_id"]]
            )

            # Insert the message into MongoDB
            result = await mongo.db.messages.insert_one(message)

            # Update conversation with last message
            await mongo.db.conversations.update_one(
                {"conversation_id": message["conversation_id"]},
                {"$set": {"last_message": message, "updated_at": datetime.utcnow()}}
            )

            return result.inserted_id
        except Exception as e:
            logger.error(f"Error inserting message: {e}")
            raise
        
    @staticmethod
    async def mark_messages_as_read(conversation_id: str, sender_id: str):
        """
        Marks all received messages as 'read'.
        """
        try:
            result = await mongo.db.messages.update_many(
                {"conversation_id": conversation_id, "sender_id": sender_id, "status": "received"},
                {"$set": {"status": "read", "read_at": datetime.now()}}
            )

            logger.info(f"✅ Marked {result.modified_count} messages as read in conversation {conversation_id}.")
            return {"updated_count": result.modified_count}
        except Exception as e:
            logger.error(f"❌ Error marking messages as read: {e}")
            raise HTTPException(status_code=500, detail="Error marking messages as read")

    @staticmethod
    async def get_messages_by_conversation(conversation_id: str):
        """
        Retrieve all messages in a conversation, sorted by timestamp.
        """
        try:
            messages_cursor = mongo.db.messages.find({"conversation_id": conversation_id}).sort("timestamp", 1)
            messages = await messages_cursor.to_list(length=1000)
            return messages
        except Exception as e:
            logger.error(f"Error fetching messages: {e}")
            raise HTTPException(status_code=500, detail="Error fetching messages")

async def initialize_database():
    """
    Initializes MongoDB collections and ensures indexes.
    """
    try:
        messages_collection = mongo.db.messages
        conversations_collection = mongo.db.conversations

        await messages_collection.create_index("message_id", unique=True)
        await conversations_collection.create_index("conversation_id", unique=True)

        logger.info("Database initialized with indexes.")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise
