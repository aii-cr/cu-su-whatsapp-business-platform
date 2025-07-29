"""
MongoDB client configuration and initialization for WhatsApp Business Platform.
Handles database connections, indexing, and collection setup.
"""

import asyncio
from typing import Optional, Dict, Any
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo import IndexModel, ASCENDING, DESCENDING, TEXT
from pymongo.errors import DuplicateKeyError, CollectionInvalid

from app.core.config import settings
from app.core.logger import logger


class DatabaseClient:
    """
    MongoDB client for the WhatsApp Business Platform.
    Manages connections, indexes, and database operations.
    """
    
    def __init__(self):
        self.client: Optional[AsyncIOMotorClient] = None
        self.db: Optional[AsyncIOMotorDatabase] = None
        self._connected = False
    
    async def connect(self) -> None:
        """
        Connect to MongoDB with proper configuration and connection pooling.
        """
        try:
            # Configure MongoDB client with optimized settings
            self.client = AsyncIOMotorClient(
                settings.MONGODB_URI,
                minPoolSize=settings.MONGODB_MIN_POOL_SIZE,
                maxPoolSize=settings.MONGODB_MAX_POOL_SIZE,
                maxIdleTimeMS=settings.MONGODB_MAX_IDLE_TIME_MS,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=10000,
                socketTimeoutMS=20000,
                retryWrites=True,
                retryReads=True
            )
            
            # Get database instance
            self.db = self.client[settings.DATABASE_NAME]
            
            # Test connection
            await self.client.admin.command('ping')
            
            self._connected = True
            logger.info(f"Successfully connected to MongoDB database: {settings.DATABASE_NAME}")
            
            # Initialize database schema and indexes
            await self._initialize_database()
            
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {str(e)}")
            raise
    
    async def disconnect(self) -> None:
        """
        Disconnect from MongoDB gracefully.
        """
        if self.client:
            self.client.close()
            self._connected = False
            logger.info("Disconnected from MongoDB")
    
    async def _initialize_database(self) -> None:
        """
        Initialize database collections and create indexes.
        """
        try:
            logger.info("Initializing database schema and indexes...")
            
            # Create indexes for all collections
            await self._create_user_indexes()
            await self._create_role_indexes()
            await self._create_permission_indexes()
            await self._create_department_indexes()
            await self._create_conversation_indexes()
            await self._create_message_indexes()
            await self._create_media_indexes()
            await self._create_tag_indexes()
            await self._create_note_indexes()
            await self._create_audit_log_indexes()
            await self._create_company_profile_indexes()
            
            logger.info("Database initialization completed successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize database: {str(e)}")
            raise
    
    async def _create_user_indexes(self) -> None:
        """Create indexes for users collection."""
        collection = self.db.users
        indexes = [
            IndexModel([("email", ASCENDING)], unique=True, name="idx_users_email"),
            IndexModel([("status", ASCENDING)], name="idx_users_status"),
            IndexModel([("department_id", ASCENDING)], name="idx_users_department"),
            IndexModel([("role_ids", ASCENDING)], name="idx_users_roles"),
            IndexModel([("is_online", ASCENDING)], name="idx_users_online"),
            IndexModel([("created_at", DESCENDING)], name="idx_users_created"),
            IndexModel([("last_seen", DESCENDING)], name="idx_users_last_seen"),
            IndexModel([("name", TEXT), ("email", TEXT)], name="idx_users_search")
        ]
        await collection.create_indexes(indexes)
        logger.info("Created indexes for users collection")
    
    async def _create_role_indexes(self) -> None:
        """Create indexes for roles collection."""
        collection = self.db.roles
        indexes = [
            IndexModel([("name", ASCENDING)], unique=True, name="idx_roles_name"),
            IndexModel([("is_active", ASCENDING)], name="idx_roles_active"),
            IndexModel([("is_system_role", ASCENDING)], name="idx_roles_system"),
            IndexModel([("permission_ids", ASCENDING)], name="idx_roles_permissions"),
            IndexModel([("created_at", DESCENDING)], name="idx_roles_created")
        ]
        await collection.create_indexes(indexes)
        logger.info("Created indexes for roles collection")
    
    async def _create_permission_indexes(self) -> None:
        """Create indexes for permissions collection."""
        collection = self.db.permissions
        indexes = [
            IndexModel([("key", ASCENDING)], unique=True, name="idx_permissions_key"),
            IndexModel([("category", ASCENDING)], name="idx_permissions_category"),
            IndexModel([("action", ASCENDING)], name="idx_permissions_action"),
            IndexModel([("resource", ASCENDING)], name="idx_permissions_resource"),
            IndexModel([("is_active", ASCENDING)], name="idx_permissions_active"),
            IndexModel([("is_system_permission", ASCENDING)], name="idx_permissions_system"),
            IndexModel([("name", TEXT), ("description", TEXT)], name="idx_permissions_search")
        ]
        await collection.create_indexes(indexes)
        logger.info("Created indexes for permissions collection")
    
    async def _create_department_indexes(self) -> None:
        """Create indexes for departments collection."""
        collection = self.db.departments
        indexes = [
            IndexModel([("name", ASCENDING)], unique=True, name="idx_departments_name"),
            IndexModel([("status", ASCENDING)], name="idx_departments_status"),
            IndexModel([("is_default", ASCENDING)], name="idx_departments_default"),
            IndexModel([("manager_id", ASCENDING)], name="idx_departments_manager"),
            IndexModel([("created_at", DESCENDING)], name="idx_departments_created"),
            IndexModel([("name", TEXT), ("display_name", TEXT)], name="idx_departments_search")
        ]
        await collection.create_indexes(indexes)
        logger.info("Created indexes for departments collection")
    
    async def _create_conversation_indexes(self) -> None:
        """Create indexes for conversations collection."""
        collection = self.db.conversations
        indexes = [
            IndexModel([("customer_phone", ASCENDING)], name="idx_conversations_customer"),
            IndexModel([("assigned_agent_id", ASCENDING)], name="idx_conversations_agent"),
            IndexModel([("department_id", ASCENDING)], name="idx_conversations_department"),
            IndexModel([("status", ASCENDING)], name="idx_conversations_status"),
            IndexModel([("priority", ASCENDING)], name="idx_conversations_priority"),
            IndexModel([("channel", ASCENDING)], name="idx_conversations_channel"),
            IndexModel([("created_at", DESCENDING)], name="idx_conversations_created"),
            IndexModel([("updated_at", DESCENDING)], name="idx_conversations_updated"),
            IndexModel([("last_activity_at", DESCENDING)], name="idx_conversations_activity"),
            IndexModel([("session_started_at", DESCENDING)], name="idx_conversations_session"),
            IndexModel([("tags", ASCENDING)], name="idx_conversations_tags"),
            IndexModel([("is_archived", ASCENDING)], name="idx_conversations_archived"),
            IndexModel([("whatsapp_conversation_id", ASCENDING)], name="idx_conversations_whatsapp"),
            IndexModel([
                ("customer_phone", ASCENDING),
                ("status", ASCENDING),
                ("updated_at", DESCENDING)
            ], name="idx_conversations_compound"),
            IndexModel([("subject", TEXT), ("initial_message", TEXT)], name="idx_conversations_search")
        ]
        await collection.create_indexes(indexes)
        logger.info("Created indexes for conversations collection")
    
    async def _create_message_indexes(self) -> None:
        """Create indexes for messages collection."""
        collection = self.db.messages
        indexes = [
            IndexModel([("conversation_id", ASCENDING), ("timestamp", DESCENDING)], 
                      name="idx_messages_conversation_time"),
            IndexModel([("sender_id", ASCENDING)], name="idx_messages_sender"),
            IndexModel([("sender_role", ASCENDING)], name="idx_messages_sender_role"),
            IndexModel([("message_type", ASCENDING)], name="idx_messages_type"),
            IndexModel([("direction", ASCENDING)], name="idx_messages_direction"),
            IndexModel([("status", ASCENDING)], name="idx_messages_status"),
            IndexModel([("timestamp", DESCENDING)], name="idx_messages_timestamp"),
            IndexModel([("created_at", DESCENDING)], name="idx_messages_created"),
            IndexModel([("whatsapp_message_id", ASCENDING)], name="idx_messages_whatsapp"),
            IndexModel([("is_flagged", ASCENDING)], name="idx_messages_flagged"),
            IndexModel([("reply_to_message_id", ASCENDING)], name="idx_messages_replies"),
            IndexModel([("text_content", TEXT), ("searchable_content", TEXT)], 
                      name="idx_messages_search")
        ]
        await collection.create_indexes(indexes)
        logger.info("Created indexes for messages collection")
    
    async def _create_media_indexes(self) -> None:
        """Create indexes for media collection."""
        collection = self.db.media
        indexes = [
            IndexModel([("conversation_id", ASCENDING)], name="idx_media_conversation"),
            IndexModel([("message_id", ASCENDING)], name="idx_media_message"),
            IndexModel([("uploaded_by", ASCENDING)], name="idx_media_uploader"),
            IndexModel([("media_type", ASCENDING)], name="idx_media_type"),
            IndexModel([("status", ASCENDING)], name="idx_media_status"),
            IndexModel([("storage_provider", ASCENDING)], name="idx_media_provider"),
            IndexModel([("created_at", DESCENDING)], name="idx_media_created"),
            IndexModel([("whatsapp_media_id", ASCENDING)], name="idx_media_whatsapp"),
            IndexModel([("content_hash", ASCENDING)], name="idx_media_hash"),
            IndexModel([("expires_at", ASCENDING)], name="idx_media_expiry"),
            IndexModel([("filename", TEXT), ("alt_text", TEXT)], name="idx_media_search")
        ]
        await collection.create_indexes(indexes)
        logger.info("Created indexes for media collection")
    
    async def _create_tag_indexes(self) -> None:
        """Create indexes for tags collection."""
        collection = self.db.tags
        indexes = [
            IndexModel([("name", ASCENDING), ("scope", ASCENDING)], 
                      unique=True, name="idx_tags_name_scope"),
            IndexModel([("tag_type", ASCENDING)], name="idx_tags_type"),
            IndexModel([("scope", ASCENDING)], name="idx_tags_scope"),
            IndexModel([("is_active", ASCENDING)], name="idx_tags_active"),
            IndexModel([("is_system_tag", ASCENDING)], name="idx_tags_system"),
            IndexModel([("parent_tag_id", ASCENDING)], name="idx_tags_parent"),
            IndexModel([("created_at", DESCENDING)], name="idx_tags_created"),
            IndexModel([("name", TEXT), ("display_name", TEXT), ("description", TEXT)], 
                      name="idx_tags_search")
        ]
        await collection.create_indexes(indexes)
        logger.info("Created indexes for tags collection")
    
    async def _create_note_indexes(self) -> None:
        """Create indexes for notes collection."""
        collection = self.db.notes
        indexes = [
            IndexModel([("entity_type", ASCENDING), ("entity_id", ASCENDING)], 
                      name="idx_notes_entity"),
            IndexModel([("conversation_id", ASCENDING)], name="idx_notes_conversation"),
            IndexModel([("message_id", ASCENDING)], name="idx_notes_message"),
            IndexModel([("author_id", ASCENDING)], name="idx_notes_author"),
            IndexModel([("note_type", ASCENDING)], name="idx_notes_type"),
            IndexModel([("priority", ASCENDING)], name="idx_notes_priority"),
            IndexModel([("visibility", ASCENDING)], name="idx_notes_visibility"),
            IndexModel([("is_pinned", ASCENDING)], name="idx_notes_pinned"),
            IndexModel([("is_resolved", ASCENDING)], name="idx_notes_resolved"),
            IndexModel([("created_at", DESCENDING)], name="idx_notes_created"),
            IndexModel([("reminder_date", ASCENDING)], name="idx_notes_reminder"),
            IndexModel([("follow_up_date", ASCENDING)], name="idx_notes_followup"),
            IndexModel([("content", TEXT), ("searchable_content", TEXT)], name="idx_notes_search")
        ]
        await collection.create_indexes(indexes)
        logger.info("Created indexes for notes collection")
    
    async def _create_audit_log_indexes(self) -> None:
        """Create indexes for audit_logs collection."""
        collection = self.db.audit_logs
        indexes = [
            # Original general audit indexes
            IndexModel([("action", ASCENDING)], name="idx_audit_action"),
            IndexModel([("user_id", ASCENDING)], name="idx_audit_user"),
            IndexModel([("resource_type", ASCENDING)], name="idx_audit_resource_type"),
            IndexModel([("resource_id", ASCENDING)], name="idx_audit_resource_id"),
            IndexModel([("conversation_id", ASCENDING)], name="idx_audit_conversation"),
            IndexModel([("timestamp", DESCENDING)], name="idx_audit_timestamp"),
            IndexModel([("date_partition", ASCENDING)], name="idx_audit_partition"),
            IndexModel([("level", ASCENDING)], name="idx_audit_level"),
            IndexModel([("success", ASCENDING)], name="idx_audit_success"),
            IndexModel([("ip_address", ASCENDING)], name="idx_audit_ip"),
            IndexModel([
                ("user_id", ASCENDING),
                ("action", ASCENDING), 
                ("timestamp", DESCENDING)
            ], name="idx_audit_compound"),
            IndexModel([("description", TEXT)], name="idx_audit_search"),
            
            # New domain-specific WhatsApp Business indexes
            IndexModel([
                ("conversation_id", ASCENDING),
                ("created_at", DESCENDING)
            ], name="idx_audit_conversation_created"),
            IndexModel([
                ("actor_id", ASCENDING),
                ("created_at", DESCENDING)
            ], name="idx_audit_actor_created"),
            IndexModel([
                ("customer_phone", ASCENDING),
                ("created_at", DESCENDING)
            ], name="idx_audit_customer_created"),
            IndexModel([
                ("department_id", ASCENDING),
                ("created_at", DESCENDING)
            ], name="idx_audit_department_created"),
            IndexModel([
                ("action", ASCENDING),
                ("created_at", DESCENDING)
            ], name="idx_audit_action_created"),
            IndexModel([("created_at", DESCENDING)], name="idx_audit_created_at")
        ]
        await collection.create_indexes(indexes)
        logger.info("Created indexes for audit_logs collection")
    
    async def _create_company_profile_indexes(self) -> None:
        """Create indexes for company_profile collection."""
        collection = self.db.company_profile
        indexes = [
            IndexModel([("name", ASCENDING)], name="idx_company_name"),
            IndexModel([("is_active", ASCENDING)], name="idx_company_active"),
            IndexModel([("is_verified", ASCENDING)], name="idx_company_verified"),
            IndexModel([("created_at", DESCENDING)], name="idx_company_created"),
            IndexModel([("updated_at", DESCENDING)], name="idx_company_updated")
        ]
        await collection.create_indexes(indexes)
        logger.info("Created indexes for company_profile collection")
    
    @property
    def is_connected(self) -> bool:
        """Check if the database client is connected."""
        return self._connected
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform a health check on the database connection.
        
        Returns:
            Dict containing health status and metrics
        """
        try:
            if not self._connected:
                return {"status": "disconnected", "error": "Not connected to database"}
            
            # Test connection with ping
            start_time = asyncio.get_event_loop().time()
            await self.client.admin.command('ping')
            response_time = (asyncio.get_event_loop().time() - start_time) * 1000  # Convert to ms
            
            # Get database stats
            stats = await self.db.command("dbStats")
            
            return {
                "status": "healthy",
                "database": settings.DATABASE_NAME,
                "response_time_ms": round(response_time, 2),
                "collections": stats.get("collections", 0),
                "data_size": stats.get("dataSize", 0),
                "storage_size": stats.get("storageSize", 0),
                "indexes": stats.get("indexes", 0)
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }

    async def get_database(self):
        """Get database instance with connection guarantee."""
        if not self._connected:
            await self.connect()
        return self.db
    
    async def __aenter__(self):
        """Async context manager entry."""
        if not self._connected:
            await self.connect()
        return self.db
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        # Don't disconnect here as it's a global instance
        pass


# Global database client instance
database = DatabaseClient() 