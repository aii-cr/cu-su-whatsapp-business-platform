"""Database helper functions for common operations."""

from typing import Optional, Dict, Any, List
from bson import ObjectId
from app.db.client import database
from app.core.logger import logger


async def get_db():
    """Get database instance with connection guarantee."""
    if not database.is_connected:
        await database.connect()
    return database.db


async def find_one(collection: str, filter_dict: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Find one document in collection."""
    db = await get_db()
    return await db[collection].find_one(filter_dict)


async def find_many(
    collection: str, 
    filter_dict: Dict[str, Any], 
    sort_by: str = "created_at",
    sort_order: int = -1,
    limit: int = 50,
    skip: int = 0
) -> List[Dict[str, Any]]:
    """Find many documents in collection with pagination."""
    db = await get_db()
    cursor = db[collection].find(filter_dict)
    cursor = cursor.sort(sort_by, sort_order).skip(skip).limit(limit)
    return await cursor.to_list(length=limit)


async def insert_one(collection: str, document: Dict[str, Any]) -> ObjectId:
    """Insert one document into collection."""
    db = await get_db()
    result = await db[collection].insert_one(document)
    return result.inserted_id


async def update_one(
    collection: str, 
    filter_dict: Dict[str, Any], 
    update_dict: Dict[str, Any]
) -> bool:
    """Update one document in collection."""
    db = await get_db()
    result = await db[collection].update_one(filter_dict, {"$set": update_dict})
    return result.modified_count > 0


async def delete_one(collection: str, filter_dict: Dict[str, Any]) -> bool:
    """Delete one document from collection."""
    db = await get_db()
    result = await db[collection].delete_one(filter_dict)
    return result.deleted_count > 0


async def count_documents(collection: str, filter_dict: Dict[str, Any]) -> int:
    """Count documents in collection."""
    db = await get_db()
    return await db[collection].count_documents(filter_dict)