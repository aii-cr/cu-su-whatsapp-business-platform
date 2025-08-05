"""
Additional database indexes for optimizing conversation and message queries.
These indexes should improve the performance of conversation loading operations.
"""

from pymongo import IndexModel, ASCENDING, DESCENDING

# Additional optimized indexes for conversation performance
CONVERSATION_PERFORMANCE_INDEXES = [
    # Compound index for conversation access with user permission checking
    IndexModel([
        ("_id", ASCENDING),
        ("assigned_agent_id", ASCENDING),
        ("created_by", ASCENDING)
    ], name="idx_conversations_access_check"),
    
    # Compound index for conversation listing with status and priority
    IndexModel([
        ("status", ASCENDING),
        ("priority", ASCENDING),
        ("updated_at", DESCENDING)
    ], name="idx_conversations_status_priority_updated"),
    
    # Index for conversation + department filtering
    IndexModel([
        ("department_id", ASCENDING),
        ("status", ASCENDING),
        ("updated_at", DESCENDING)
    ], name="idx_conversations_dept_status_updated"),
    
    # Index optimized for agent dashboard view
    IndexModel([
        ("assigned_agent_id", ASCENDING),
        ("status", ASCENDING),
        ("last_activity_at", DESCENDING)
    ], name="idx_conversations_agent_activity"),
]

# Additional optimized indexes for message performance  
MESSAGE_PERFORMANCE_INDEXES = [
    # Optimized compound index for conversation messages with timestamp
    # This supports both pagination and counting efficiently
    IndexModel([
        ("conversation_id", ASCENDING),
        ("timestamp", DESCENDING),
        ("_id", ASCENDING)  # For stable pagination
    ], name="idx_messages_conversation_time_id"),
    
    # Index for message status tracking and analytics
    IndexModel([
        ("conversation_id", ASCENDING),
        ("status", ASCENDING),
        ("direction", ASCENDING),
        ("timestamp", DESCENDING)
    ], name="idx_messages_conversation_status_dir"),
    
    # Index for recent messages across all conversations (dashboard)
    IndexModel([
        ("timestamp", DESCENDING),
        ("conversation_id", ASCENDING),
        ("direction", ASCENDING)
    ], name="idx_messages_recent_global"),
    
    # Sparse index for WhatsApp message ID lookups
    IndexModel([
        ("whatsapp_message_id", ASCENDING)
    ], name="idx_messages_whatsapp_id", sparse=True),
]

# Cache-optimized queries
OPTIMIZED_AGGREGATION_PIPELINES = {
    "conversation_with_recent_messages": [
        # This pipeline efficiently gets conversation + recent messages
        {
            "$match": {
                "_id": "$conversation_id_placeholder"
            }
        },
        {
            "$lookup": {
                "from": "messages",
                "let": {"conv_id": "$_id"},
                "pipeline": [
                    {"$match": {"$expr": {"$eq": ["$conversation_id", "$$conv_id"]}}},
                    {"$sort": {"timestamp": -1}},
                    {"$limit": 50},
                    {"$sort": {"timestamp": 1}}  # Restore chronological order
                ],
                "as": "recent_messages"
            }
        },
        {
            "$lookup": {
                "from": "messages",
                "let": {"conv_id": "$_id"},
                "pipeline": [
                    {"$match": {"$expr": {"$eq": ["$conversation_id", "$$conv_id"]}}},
                    {"$count": "total"}
                ],
                "as": "message_count"
            }
        },
        {
            "$addFields": {
                "total_messages": {"$arrayElemAt": ["$message_count.total", 0]}
            }
        },
        {
            "$project": {
                "message_count": 0  # Remove helper field
            }
        }
    ],
    
    "conversation_list_with_last_message": [
        # Optimized pipeline for conversation list with last message preview
        {
            "$match": {
                # Dynamic filters will be added here
            }
        },
        {
            "$lookup": {
                "from": "messages",
                "let": {"conv_id": "$_id"},
                "pipeline": [
                    {"$match": {"$expr": {"$eq": ["$conversation_id", "$$conv_id"]}}},
                    {"$sort": {"timestamp": -1}},
                    {"$limit": 1}
                ],
                "as": "last_message"
            }
        },
        {
            "$addFields": {
                "last_message": {"$arrayElemAt": ["$last_message", 0]}
            }
        },
        {
            "$sort": {"updated_at": -1}
        }
    ]
}

async def create_performance_indexes(db):
    """
    Create additional performance indexes for conversations and messages.
    
    Args:
        db: MongoDB database instance
    """
    # Create conversation performance indexes
    try:
        conversation_collection = db.conversations
        await conversation_collection.create_indexes(CONVERSATION_PERFORMANCE_INDEXES)
        print("✅ Created conversation performance indexes")
    except Exception as e:
        print(f"❌ Error creating conversation indexes: {e}")
    
    # Create message performance indexes
    try:
        message_collection = db.messages
        await message_collection.create_indexes(MESSAGE_PERFORMANCE_INDEXES)
        print("✅ Created message performance indexes")
    except Exception as e:
        print(f"❌ Error creating message indexes: {e}")

async def analyze_query_performance(db, conversation_id: str):
    """
    Analyze query performance for conversation loading.
    
    Args:
        db: MongoDB database instance
        conversation_id: ID to test with
    """
    import time
    
    print("🔍 Analyzing conversation loading performance...")
    
    # Test 1: Single conversation query
    start_time = time.time()
    conversation = await db.conversations.find_one({"_id": conversation_id})
    conv_time = (time.time() - start_time) * 1000
    print(f"📊 Conversation query: {conv_time:.2f}ms")
    
    # Test 2: Messages query with pagination
    start_time = time.time()
    messages = await db.messages.find(
        {"conversation_id": conversation_id}
    ).sort("timestamp", -1).limit(50).to_list(50)
    msg_time = (time.time() - start_time) * 1000
    print(f"📊 Messages query: {msg_time:.2f}ms")
    
    # Test 3: Message count query
    start_time = time.time()
    count = await db.messages.count_documents({"conversation_id": conversation_id})
    count_time = (time.time() - start_time) * 1000
    print(f"📊 Message count query: {count_time:.2f}ms")
    
    # Test 4: Combined aggregation (optimized)
    start_time = time.time()
    pipeline = [
        {"$match": {"conversation_id": conversation_id}},
        {
            "$facet": {
                "messages": [
                    {"$sort": {"timestamp": -1}},
                    {"$limit": 50},
                    {"$sort": {"timestamp": 1}}
                ],
                "total_count": [{"$count": "count"}]
            }
        }
    ]
    result = await db.messages.aggregate(pipeline).to_list(1)
    agg_time = (time.time() - start_time) * 1000
    print(f"📊 Optimized aggregation: {agg_time:.2f}ms")
    
    total_separate = conv_time + msg_time + count_time
    improvement = ((total_separate - agg_time) / total_separate) * 100
    
    print(f"\n📈 Performance Summary:")
    print(f"   Separate queries total: {total_separate:.2f}ms")
    print(f"   Optimized approach: {agg_time:.2f}ms")
    print(f"   Performance improvement: {improvement:.1f}%")
    
    return {
        "separate_queries_ms": total_separate,
        "optimized_query_ms": agg_time,
        "improvement_percent": improvement
    }