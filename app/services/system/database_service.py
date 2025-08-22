from datetime import datetime
from fastapi import HTTPException
from bson.objectid import ObjectId
from app.core.logger import logger
from app.services.base_service import BaseService

class ChatPlatformService(BaseService):
    """Service for managing chat platform database operations."""
    
    async def create_conversation(self, conversation_id: str, participants: list):
        """
        Create a new conversation if it doesn't exist.
        """
        db = await self._get_db()
        
        existing_conversation = await db.conversations.find_one({"conversation_id": conversation_id})
        if not existing_conversation:
            conversation_data = {
                "conversation_id": conversation_id,
                "participants": participants,
                "last_message": None,
                "created_at": datetime.now(),
                "updated_at": datetime.now()
            }
            await db.conversations.insert_one(conversation_data)
            logger.info(f"Created new conversation: {conversation_id}")

    async def create_message(self, message: dict):
        """
        Save a message and ensure conversation exists.
        """
        try:
            db = await self._get_db()
            
            # Convert WhatsApp timestamp (Unix timestamp string) to datetime
            if "timestamp" in message and isinstance(message["timestamp"], str):
                message["timestamp"] = datetime.fromtimestamp(int(message["timestamp"]))

            # Ensure the conversation exists before adding the message
            await self.create_conversation(
                message["conversation_id"], 
                [message["sender_id"], message["receiver_id"]]
            )

            # Insert the message into MongoDB
            result = await db.messages.insert_one(message)

            # Update conversation with last message
            await db.conversations.update_one(
                {"conversation_id": message["conversation_id"]},
                {"$set": {"last_message": message, "updated_at": datetime.now(datetime.UTC)}}
            )

            return result.inserted_id
        except Exception as e:
            logger.error(f"Error inserting message: {e}")
            raise
        
    async def mark_messages_as_read(self, conversation_id: str, sender_id: str):
        """
        Marks all received messages as 'read'.
        """
        try:
            db = await self._get_db()
            
            result = await db.messages.update_many(
                {"conversation_id": conversation_id, "sender_id": sender_id, "status": "received"},
                {"$set": {"status": "read", "read_at": datetime.now()}}
            )

            logger.info(f"✅ Marked {result.modified_count} messages as read in conversation {conversation_id}.")
            return {"updated_count": result.modified_count}
        except Exception as e:
            logger.error(f"❌ Error marking messages as read: {e}")
            raise HTTPException(status_code=500, detail="Error marking messages as read")

    async def get_messages_by_conversation(self, conversation_id: str):
        """
        Retrieve all messages in a conversation, sorted by timestamp.
        """
        try:
            db = await self._get_db()
            
            messages_cursor = db.messages.find({"conversation_id": conversation_id}).sort("timestamp", 1)
            messages = await messages_cursor.to_list(length=1000)
            return messages
        except Exception as e:
            logger.error(f"Error fetching messages: {e}")
            raise HTTPException(status_code=500, detail="Error fetching messages")

    async def initialize_database(self):
        """
        Initializes MongoDB collections and ensures indexes.
        """
        try:
            db = await self._get_db()
            
            messages_collection = db.messages
            conversations_collection = db.conversations

            await messages_collection.create_index("message_id", unique=True)
            await conversations_collection.create_index("conversation_id", unique=True)

            logger.info("Database initialized with indexes.")
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            raise

# Global database service instance
database_service = ChatPlatformService()
