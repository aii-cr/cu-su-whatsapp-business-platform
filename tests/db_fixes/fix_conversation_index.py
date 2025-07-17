#!/usr/bin/env python3
"""
Script to fix the conversation_id unique index issue.
This removes the problematic unique index that's causing duplicate key errors.
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings
from app.core.logger import logger

async def fix_conversation_index():
    """Remove the problematic unique index on conversation_id."""
    client = None
    try:
        # Connect to MongoDB
        client = AsyncIOMotorClient(settings.MONGODB_URI)
        db = client[settings.DATABASE_NAME]
        
        logger.info("🔧 [FIX_INDEX] Starting conversation index fix...")
        
        # Check if the problematic index exists
        indexes = await db.conversations.list_indexes().to_list(None)
        conversation_id_index = None
        
        for index in indexes:
            if index.get("name") == "conversation_id_1":
                conversation_id_index = index
                break
        
        if conversation_id_index:
            logger.info("🔧 [FIX_INDEX] Found problematic unique index on conversation_id, removing...")
            await db.conversations.drop_index("conversation_id_1")
            logger.info("✅ [FIX_INDEX] Successfully removed conversation_id unique index")
        else:
            logger.info("ℹ️ [FIX_INDEX] No problematic conversation_id index found")
        
        # List remaining indexes for verification
        remaining_indexes = await db.conversations.list_indexes().to_list(None)
        logger.info(f"📋 [FIX_INDEX] Remaining indexes: {[idx.get('name') for idx in remaining_indexes]}")
        
    except Exception as e:
        logger.error(f"❌ [FIX_INDEX] Failed to fix conversation index: {str(e)}")
        raise
    finally:
        if client:
            client.close()

if __name__ == "__main__":
    asyncio.run(fix_conversation_index()) 