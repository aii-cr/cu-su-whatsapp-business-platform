#!/usr/bin/env python3
"""
Script to fix the message_id unique index issue.
This removes the problematic unique index that's causing duplicate key errors.
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings
from app.core.logger import logger

async def fix_message_index():
    """Remove the problematic unique index on message_id."""
    client = None
    try:
        # Connect to MongoDB
        client = AsyncIOMotorClient(settings.MONGODB_URI)
        db = client[settings.DATABASE_NAME]
        
        logger.info("🔧 [FIX_MESSAGE_INDEX] Starting message index fix...")
        
        # Check if the problematic index exists
        indexes = await db.messages.list_indexes().to_list(None)
        message_id_index = None
        
        for index in indexes:
            if index.get("name") == "message_id_1":
                message_id_index = index
                break
        
        if message_id_index:
            logger.info("🔧 [FIX_MESSAGE_INDEX] Found problematic unique index on message_id, removing...")
            await db.messages.drop_index("message_id_1")
            logger.info("✅ [FIX_MESSAGE_INDEX] Successfully removed message_id unique index")
        else:
            logger.info("ℹ️ [FIX_MESSAGE_INDEX] No problematic message_id index found")
        
        # List remaining indexes for verification
        remaining_indexes = await db.messages.list_indexes().to_list(None)
        logger.info(f"📋 [FIX_MESSAGE_INDEX] Remaining indexes: {[idx.get('name') for idx in remaining_indexes]}")
        
    except Exception as e:
        logger.error(f"❌ [FIX_MESSAGE_INDEX] Failed to fix message index: {str(e)}")
        raise
    finally:
        if client:
            client.close()

if __name__ == "__main__":
    asyncio.run(fix_message_index()) 