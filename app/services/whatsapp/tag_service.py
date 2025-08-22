"""Enhanced tag service following project patterns."""

from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from bson import ObjectId
from pymongo import DESCENDING, ASCENDING

from app.services.base_service import BaseService
from app.core.logger import logger
from app.schemas.whatsapp.chat.tag import TagCreate, TagUpdate, TagStatus, TagCategory
from app.db.models.whatsapp.chat.tag import Tag, generate_slug


class TagService(BaseService):
    """Enhanced tag service for conversation tags."""
    
    def __init__(self):
        super().__init__()
    
    async def create_tag(self, tag_data: TagCreate, created_by: ObjectId) -> Dict[str, Any]:
        """Create a new tag."""
        db = await self._get_db()
        
        try:
            # Generate slug
            slug = generate_slug(tag_data.name)
            
            # Check if tag name or slug already exists
            existing = await db.tags.find_one({
                "$or": [
                    {"name": {"$regex": f"^{tag_data.name}$", "$options": "i"}},
                    {"slug": slug}
                ]
            })
            if existing:
                raise ValueError(f"Tag '{tag_data.name}' already exists")
            
            # Create tag document
            now = datetime.now(timezone.utc)
            tag_doc = {
                "name": tag_data.name,
                "slug": slug,
                "display_name": tag_data.name,
                "description": tag_data.description,
                "category": tag_data.category or TagCategory.GENERAL,
                "color": tag_data.color,
                "parent_tag_id": None,
                "child_tags": [],
                "status": TagStatus.ACTIVE,
                "is_system_tag": False,
                "is_auto_assignable": True,
                "usage_count": 0,
                "department_ids": [],
                "user_ids": [],
                "created_at": now,
                "updated_at": now,
                "created_by": created_by,
                "updated_by": created_by
            }
            
            result = await db.tags.insert_one(tag_doc)
            tag_doc["_id"] = result.inserted_id
            
            logger.info(f"Created tag: {tag_data.name} (ID: {result.inserted_id})")
            return tag_doc
            
        except Exception as e:
            logger.error(f"Error creating tag: {str(e)}")
            raise
    
    async def get_tag(self, tag_id: ObjectId) -> Optional[Dict[str, Any]]:
        """Get a single tag by ID."""
        db = await self._get_db()
        
        try:
            tag = await db.tags.find_one({"_id": tag_id})
            return tag
        except Exception as e:
            logger.error(f"Error getting tag: {str(e)}")
            raise
    
    async def update_tag(self, tag_id: ObjectId, tag_data: TagUpdate, updated_by: ObjectId) -> Optional[Dict[str, Any]]:
        """Update an existing tag."""
        db = await self._get_db()
        
        try:
            # Build update document
            update_doc = {"updated_at": datetime.now(timezone.utc), "updated_by": updated_by}
            
            if tag_data.name is not None:
                # Check if new name conflicts
                existing = await db.tags.find_one({
                    "_id": {"$ne": tag_id},
                    "name": {"$regex": f"^{tag_data.name}$", "$options": "i"}
                })
                if existing:
                    raise ValueError(f"Tag '{tag_data.name}' already exists")
                
                update_doc["name"] = tag_data.name
                update_doc["slug"] = generate_slug(tag_data.name)
                update_doc["display_name"] = tag_data.name
            
            if tag_data.color is not None:
                update_doc["color"] = tag_data.color
            
            if tag_data.category is not None:
                update_doc["category"] = tag_data.category
                
            if tag_data.description is not None:
                update_doc["description"] = tag_data.description
                
            if tag_data.status is not None:
                update_doc["status"] = tag_data.status
            
            result = await db.tags.update_one(
                {"_id": tag_id},
                {"$set": update_doc}
            )
            
            if result.matched_count == 0:
                return None
                
            # Return updated tag
            return await db.tags.find_one({"_id": tag_id})
            
        except Exception as e:
            logger.error(f"Error updating tag: {str(e)}")
            raise
    
    async def delete_tag(self, tag_id: ObjectId) -> bool:
        """Soft delete a tag."""
        db = await self._get_db()
        
        try:
            result = await db.tags.update_one(
                {"_id": tag_id},
                {"$set": {"status": TagStatus.INACTIVE, "updated_at": datetime.now(timezone.utc)}}
            )
            return result.matched_count > 0
        except Exception as e:
            logger.error(f"Error deleting tag: {str(e)}")
            raise
    
    async def list_tags(
        self, 
        limit: int = 20,
        offset: int = 0,
        search: Optional[str] = None,
        category: Optional[str] = None,
        status: str = TagStatus.ACTIVE,
        sort_by: str = "usage_count",
        sort_order: str = "desc"
    ) -> tuple[List[Dict[str, Any]], int]:
        """List tags with filtering and pagination."""
        db = await self._get_db()
        
        try:
            # Build filter query
            filter_query = {"status": status}
            
            if search:
                filter_query["$or"] = [
                    {"name": {"$regex": search, "$options": "i"}},
                    {"description": {"$regex": search, "$options": "i"}}
                ]
            
            if category:
                filter_query["category"] = category
            
            # Get total count
            total = await db.tags.count_documents(filter_query)
            
            # Build sort order
            sort_direction = DESCENDING if sort_order == "desc" else ASCENDING
            
            # Get tags with pagination
            cursor = (db.tags.find(filter_query)
                     .sort(sort_by, sort_direction)
                     .skip(offset)
                     .limit(limit))
            
            tags = await cursor.to_list(length=limit)
            
            return tags, total
            
        except Exception as e:
            logger.error(f"Error listing tags: {str(e)}")
            raise
    
    async def search_tags(self, query: str = "", limit: int = 10) -> List[Dict[str, Any]]:
        """Search tags by name or return popular tags."""
        db = await self._get_db()
        
        try:
            if query.strip():
                # Search by name
                filter_query = {
                    "status": TagStatus.ACTIVE,
                    "name": {"$regex": query, "$options": "i"}
                }
            else:
                # Return popular tags
                filter_query = {
                    "status": TagStatus.ACTIVE,
                    "usage_count": {"$gt": 0}
                }
            
            cursor = db.tags.find(filter_query).sort("usage_count", DESCENDING).limit(limit)
            tags = await cursor.to_list(length=limit)
            
            return tags
            
        except Exception as e:
            logger.error(f"Error searching tags: {str(e)}")
            raise
    
    async def suggest_tags(
        self,
        query: str = "",
        limit: int = 10,
        category: Optional[str] = None,
        exclude_ids: List[ObjectId] = None
    ) -> List[Dict[str, Any]]:
        """Get tag suggestions for autocomplete."""
        db = await self._get_db()
        
        try:
            filter_query = {
                "status": TagStatus.ACTIVE,
                "is_auto_assignable": True
            }
            
            if query.strip():
                filter_query["name"] = {"$regex": query, "$options": "i"}
            
            if category:
                filter_query["category"] = category
                
            if exclude_ids:
                filter_query["_id"] = {"$nin": exclude_ids}
            
            cursor = (db.tags.find(filter_query)
                     .sort([("usage_count", DESCENDING), ("name", ASCENDING)])
                     .limit(limit))
            
            tags = await cursor.to_list(length=limit)
            
            return tags
            
        except Exception as e:
            logger.error(f"Error getting tag suggestions: {str(e)}")
            raise

    async def get_quick_add_tags(self, limit: int = 7) -> List[Dict[str, Any]]:
        """Get most frequently used tags for quick selection."""
        db = await self._get_db()
        
        try:
            filter_query = {
                "status": TagStatus.ACTIVE,
                "is_auto_assignable": True,
            }
            
            cursor = (db.tags.find(filter_query)
                     .sort([("usage_count", DESCENDING), ("name", ASCENDING)])
                     .limit(limit))
            
            tags = await cursor.to_list(length=limit)
            
            return tags
            
        except Exception as e:
            logger.error(f"Error getting quick add tags: {str(e)}")
            raise
    
    async def assign_tags(self, conversation_id: ObjectId, tag_ids: List[ObjectId], assigned_by: ObjectId, auto_assigned: bool = False) -> List[Dict[str, Any]]:
        """Assign tags to conversation."""
        db = await self._get_db()
        
        try:
            # Get tags
            tags = await db.tags.find({"_id": {"$in": tag_ids}, "status": TagStatus.ACTIVE}).to_list(length=len(tag_ids))
            if len(tags) != len(tag_ids):
                raise ValueError("Some tags not found or inactive")
            
            # Check for existing assignments
            existing = await db.conversation_tags.find({
                "conversation_id": conversation_id,
                "tag_id": {"$in": tag_ids}
            }).to_list(length=None)
            
            existing_tag_ids = {doc["tag_id"] for doc in existing}
            new_tag_ids = [tid for tid in tag_ids if tid not in existing_tag_ids]
            
            if not new_tag_ids:
                return []
            
            # Create assignments
            now = datetime.now(timezone.utc)
            assignments = []
            
            for tag in tags:
                if tag["_id"] in new_tag_ids:
                    assignment = {
                        "conversation_id": conversation_id,
                        "tag_id": tag["_id"],
                        "tag_name": tag["name"],
                        "tag_slug": tag["slug"],
                        "tag_color": tag["color"],
                        "tag_category": tag["category"],
                        "assigned_at": now,
                        "assigned_by": assigned_by,
                        "auto_assigned": auto_assigned
                    }
                    assignments.append(assignment)
            
            if assignments:
                await db.conversation_tags.insert_many(assignments)
                
                # Update usage counts
                await db.tags.update_many(
                    {"_id": {"$in": new_tag_ids}},
                    {"$inc": {"usage_count": 1}, "$set": {"updated_at": now}}
                )
            
            logger.info(f"Assigned {len(assignments)} tags to conversation {conversation_id}")
            return assignments
            
        except Exception as e:
            logger.error(f"Error assigning tags: {str(e)}")
            raise
    
    async def unassign_tags(self, conversation_id: ObjectId, tag_ids: List[ObjectId]) -> int:
        """Unassign tags from conversation."""
        db = await self._get_db()
        
        try:
            result = await db.conversation_tags.delete_many({
                "conversation_id": conversation_id,
                "tag_id": {"$in": tag_ids}
            })
            
            if result.deleted_count > 0:
                # Update usage counts
                await db.tags.update_many(
                    {"_id": {"$in": tag_ids}},
                    {
                        "$inc": {"usage_count": -1},
                        "$set": {"updated_at": datetime.now(timezone.utc)}
                    }
                )
                
                # Ensure counts don't go negative
                await db.tags.update_many(
                    {"_id": {"$in": tag_ids}, "usage_count": {"$lt": 0}},
                    {"$set": {"usage_count": 0}}
                )
            
            logger.info(f"Unassigned {result.deleted_count} tags from conversation {conversation_id}")
            return result.deleted_count
            
        except Exception as e:
            logger.error(f"Error unassigning tags: {str(e)}")
            raise
    
    async def get_conversation_tags(self, conversation_id: ObjectId) -> List[Dict[str, Any]]:
        """Get tags assigned to a conversation."""
        db = await self._get_db()
        
        try:
            tags = await db.conversation_tags.find({
                "conversation_id": conversation_id
            }).sort("assigned_at", 1).to_list(length=None)
            
            return tags
            
        except Exception as e:
            logger.error(f"Error getting conversation tags: {str(e)}")
            raise
    
    async def get_tag_settings(self) -> Dict[str, Any]:
        """Get tag-related settings."""
        from app.core.config import settings
        return {
            "max_tags_per_conversation": settings.MAX_TAGS_PER_CONVERSATION,
            "quick_add_tags_limit": settings.QUICK_ADD_TAGS_LIMIT
        }


# Global service instance
tag_service = TagService()