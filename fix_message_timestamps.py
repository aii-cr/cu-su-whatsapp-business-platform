#!/usr/bin/env python3
"""
Script to fix existing message timestamps in the database.
Subtracts 6 hours from all message timestamps to correct the timezone conversion issue.
"""

import asyncio
from datetime import datetime, timedelta, timezone
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId

# MongoDB connection
MONGO_URI = "mongodb://steve_aii:tm4aC359j05AF@172.20.5.20:45017/chat_platform?authSource=chat_platform"

async def fix_message_timestamps():
    """Fix existing message timestamps by subtracting 6 hours."""
    
    # Connect to MongoDB
    client = AsyncIOMotorClient(MONGO_URI)
    db = client.chat_platform
    
    print("🔧 Fixing message timestamps...")
    
    # Get all messages
    messages = await db.messages.find({}).to_list(None)
    print(f"📊 Found {len(messages)} messages to process")
    
    fixed_count = 0
    for message in messages:
        try:
            # Get current timestamps
            timestamp = message.get('timestamp')
            created_at = message.get('created_at')
            updated_at = message.get('updated_at')
            
            # Check if timestamps need fixing (if they're in the future)
            now = datetime.utcnow()
            needs_fixing = False
            
            if timestamp and timestamp > now + timedelta(hours=1):
                needs_fixing = True
            if created_at and created_at > now + timedelta(hours=1):
                needs_fixing = True
            if updated_at and updated_at > now + timedelta(hours=1):
                needs_fixing = True
            
            if needs_fixing:
                # Subtract 6 hours from timestamps
                update_data = {}
                
                if timestamp:
                    update_data['timestamp'] = timestamp - timedelta(hours=6)
                if created_at:
                    update_data['created_at'] = created_at - timedelta(hours=6)
                if updated_at:
                    update_data['updated_at'] = updated_at - timedelta(hours=6)
                
                # Also fix sent_at, delivered_at, read_at if they exist
                for field in ['sent_at', 'delivered_at', 'read_at']:
                    if message.get(field):
                        update_data[field] = message[field] - timedelta(hours=6)
                
                # Update the message
                await db.messages.update_one(
                    {'_id': message['_id']},
                    {'$set': update_data}
                )
                
                fixed_count += 1
                print(f"✅ Fixed message {message['_id']}: {timestamp} → {update_data.get('timestamp')}")
        
        except Exception as e:
            print(f"❌ Error fixing message {message.get('_id')}: {e}")
    
    print(f"🎉 Fixed {fixed_count} messages out of {len(messages)} total messages")
    
    # Close connection
    client.close()

if __name__ == "__main__":
    asyncio.run(fix_message_timestamps())
