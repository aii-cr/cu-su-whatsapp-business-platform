"""
Tag Service for managing conversation tags.
Handles CRUD operations, suggestions, and conversation tag assignments.
"""

from datetime import datetime, timezone
from typing import Optional, Dict, Any, List, Tuple
from bson import ObjectId
from pymongo import ASCENDING, DESCENDING, TEXT
from pymongo.errors import DuplicateKeyError

from app.services.base_service import BaseService
from app.core.logger import logger
from app.config.error_codes import ErrorCode, get_error_response
from app.db.models.whatsapp.chat.tag import (
    Tag, TagDenormalized, ConversationTag, TagStatus, TagCategory, TagColor
)
from app.schemas.whatsapp.chat.tag import (
    TagCreate, TagUpdate, TagListRequest, TagSuggestRequest,
    generate_slug
)


class TagService(BaseService):
    """Service for managing conversation tags."""
    
    def __init__(self):
        super().__init__()
    
    async def create_tag(
        self,
        tag_data: TagCreate,
        created_by: ObjectId
    ) -> Dict[str, Any]:
        """
        Create a new tag.
        
        Args:
            tag_data: Tag creation data
            created_by: User ID who is creating the tag
            
        Returns:
            Created tag document
            
        Raises:
            ValueError: If tag name already exists or validation fails
        """
        db = await self._get_db()
        
        try:
            # Generate slug from name
            slug = generate_slug(tag_data.name)
            
            # Check for duplicate slug (case-insensitive)
            existing_tag = await db.tags.find_one({"slug": {"$regex": f"^{slug}$", "$options": "i"}})
            if existing_tag:
                raise ValueError(f"A tag with name '{tag_data.name}' already exists")
            
            # Validate parent tag if specified
            parent_tag = None
            if tag_data.parent_tag_id:
                parent_tag = await db.tags.find_one({
                    "_id": ObjectId(tag_data.parent_tag_id),
                    "status": TagStatus.ACTIVE
                })
                if not parent_tag:
                    raise ValueError("Parent tag not found or inactive")
            
            # Validate department and user IDs if specified
            if tag_data.department_ids:
                dept_count = await db.departments.count_documents({
                    "_id": {"$in": [ObjectId(did) for did in tag_data.department_ids]},
                    "status": "active"
                })
                if dept_count != len(tag_data.department_ids):
                    raise ValueError("One or more department IDs are invalid")
            
            if tag_data.user_ids:
                user_count = await db.users.count_documents({
                    "_id": {"$in": [ObjectId(uid) for uid in tag_data.user_ids]},
                    "status": "active"
                })
                if user_count != len(tag_data.user_ids):
                    raise ValueError("One or more user IDs are invalid")
            
            # Create tag document
            now = datetime.utcnow()
            tag_doc = {
                "name": tag_data.name,
                "slug": slug,
                "display_name": tag_data.display_name or tag_data.name,
                "description": tag_data.description,
                "category": tag_data.category,
                "color": tag_data.color,
                "parent_tag_id": ObjectId(tag_data.parent_tag_id) if tag_data.parent_tag_id else None,
                "child_tags": [],
                "status": TagStatus.ACTIVE,
                "is_system_tag": False,
                "is_auto_assignable": tag_data.is_auto_assignable,
                "usage_count": 0,
                "department_ids": [ObjectId(did) for did in tag_data.department_ids],
                "user_ids": [ObjectId(uid) for uid in tag_data.user_ids],
                "created_at": now,
                "updated_at": now,
                "created_by": created_by,
                "updated_by": created_by
            }
            
            # Insert tag
            result = await db.tags.insert_one(tag_doc)
            tag_doc["_id"] = result.inserted_id
            
            # Update parent tag's child_tags if needed
            if parent_tag:
                await db.tags.update_one(
                    {"_id": parent_tag["_id"]},
                    {
                        "$addToSet": {"child_tags": result.inserted_id},
                        "$set": {"updated_at": now, "updated_by": created_by}
                    }
                )
            
            logger.info(f"Created tag: {tag_data.name} (ID: {result.inserted_id})")
            return tag_doc
            
        except DuplicateKeyError:
            raise ValueError(f"A tag with name '{tag_data.name}' already exists")
        except Exception as e:
            logger.error(f"Error creating tag: {str(e)}")
            raise
    
    async def get_tag(self, tag_id: ObjectId) -> Optional[Dict[str, Any]]:
        """Get tag by ID."""
        db = await self._get_db()
        
        try:
            tag = await db.tags.find_one({"_id": tag_id})
            return tag
        except Exception as e:
            logger.error(f"Error getting tag {tag_id}: {str(e)}")
            raise
    
    async def get_tag_by_slug(self, slug: str) -> Optional[Dict[str, Any]]:
        """Get tag by slug (case-insensitive)."""
        db = await self._get_db()
        
        try:
            tag = await db.tags.find_one({"slug": {"$regex": f"^{slug}$", "$options": "i"}})
            return tag
        except Exception as e:
            logger.error(f"Error getting tag by slug {slug}: {str(e)}")
            raise
    
    async def update_tag(
        self,
        tag_id: ObjectId,
        tag_data: TagUpdate,
        updated_by: ObjectId
    ) -> Optional[Dict[str, Any]]:
        """
        Update an existing tag.
        
        Args:
            tag_id: Tag ID to update
            tag_data: Update data
            updated_by: User ID performing the update
            
        Returns:
            Updated tag document or None if not found
        """
        db = await self._get_db()
        
        try:
            # Get existing tag
            existing_tag = await db.tags.find_one({"_id": tag_id})
            if not existing_tag:
                return None
            
            # Build update document
            update_doc = {"updated_at": datetime.utcnow(), "updated_by": updated_by}
            
            # Update name and slug if name changed
            if tag_data.name and tag_data.name != existing_tag["name"]:
                new_slug = generate_slug(tag_data.name)
                
                # Check for duplicate slug
                duplicate = await db.tags.find_one({
                    "_id": {"$ne": tag_id},
                    "slug": {"$regex": f"^{new_slug}$", "$options": "i"}
                })
                if duplicate:
                    raise ValueError(f"A tag with name '{tag_data.name}' already exists")
                
                update_doc["name"] = tag_data.name
                update_doc["slug"] = new_slug
            
            # Update other fields
            for field in ["display_name", "description", "category", "color", "is_auto_assignable", "status"]:
                value = getattr(tag_data, field, None)
                if value is not None:
                    update_doc[field] = value
            
            # Handle parent tag changes
            if hasattr(tag_data, 'parent_tag_id') and tag_data.parent_tag_id is not None:
                if tag_data.parent_tag_id:
                    # Validate new parent tag
                    parent_tag = await db.tags.find_one({
                        "_id": ObjectId(tag_data.parent_tag_id),
                        "status": TagStatus.ACTIVE
                    })
                    if not parent_tag:
                        raise ValueError("Parent tag not found or inactive")
                    
                    # Check for circular reference
                    if str(parent_tag["_id"]) == str(tag_id):
                        raise ValueError("Tag cannot be its own parent")
                    
                    update_doc["parent_tag_id"] = ObjectId(tag_data.parent_tag_id)
                else:
                    update_doc["parent_tag_id"] = None
            
            # Handle department and user restrictions
            if tag_data.department_ids is not None:
                if tag_data.department_ids:
                    dept_count = await db.departments.count_documents({
                        "_id": {"$in": [ObjectId(did) for did in tag_data.department_ids]},
                        "status": "active"
                    })
                    if dept_count != len(tag_data.department_ids):
                        raise ValueError("One or more department IDs are invalid")
                update_doc["department_ids"] = [ObjectId(did) for did in tag_data.department_ids]
            
            if tag_data.user_ids is not None:
                if tag_data.user_ids:
                    user_count = await db.users.count_documents({
                        "_id": {"$in": [ObjectId(uid) for uid in tag_data.user_ids]},
                        "status": "active"
                    })
                    if user_count != len(tag_data.user_ids):
                        raise ValueError("One or more user IDs are invalid")
                update_doc["user_ids"] = [ObjectId(uid) for uid in tag_data.user_ids]
            
            # Update tag
            result = await db.tags.update_one(
                {"_id": tag_id},
                {"$set": update_doc}
            )
            
            if result.modified_count == 0:
                return None
            
            # Get updated tag
            updated_tag = await db.tags.find_one({"_id": tag_id})
            
            # If tag was deactivated, update denormalized data in conversations
            if tag_data.status == TagStatus.INACTIVE:
                await self._update_conversation_tag_denorm(tag_id, updated_tag)
            
            logger.info(f"Updated tag: {tag_id}")
            return updated_tag
            
        except Exception as e:
            logger.error(f"Error updating tag {tag_id}: {str(e)}")
            raise
    
    async def delete_tag(self, tag_id: ObjectId, deleted_by: ObjectId) -> bool:
        """
        Delete a tag (soft delete by setting status to inactive).
        
        Args:
            tag_id: Tag ID to delete
            deleted_by: User ID performing the deletion
            
        Returns:
            True if deleted, False if not found
        """
        db = await self._get_db()
        
        try:
            # Check if tag exists and is not a system tag
            tag = await db.tags.find_one({"_id": tag_id})
            if not tag:
                return False
            
            if tag.get("is_system_tag", False):
                raise ValueError("Cannot delete system tags")
            
            # Check if tag has children
            child_count = await db.tags.count_documents({"parent_tag_id": tag_id})
            if child_count > 0:
                raise ValueError("Cannot delete tag with child tags")
            
            # Soft delete (set status to inactive)
            result = await db.tags.update_one(
                {"_id": tag_id},
                {
                    "$set": {
                        "status": TagStatus.INACTIVE,
                        "updated_at": datetime.utcnow(),
                        "updated_by": deleted_by
                    }
                }
            )
            
            if result.modified_count > 0:
                # Update denormalized data in conversations
                updated_tag = await db.tags.find_one({"_id": tag_id})
                await self._update_conversation_tag_denorm(tag_id, updated_tag)
                
                # Remove from parent's child_tags if applicable
                if tag.get("parent_tag_id"):
                    await db.tags.update_one(
                        {"_id": tag["parent_tag_id"]},
                        {"$pull": {"child_tags": tag_id}}
                    )
                
                logger.info(f"Deactivated tag: {tag_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error deleting tag {tag_id}: {str(e)}")
            raise
    
    async def list_tags(self, request: TagListRequest) -> Tuple[List[Dict[str, Any]], int]:
        """
        List tags with filtering, searching, and pagination.
        
        Args:
            request: List request parameters
            
        Returns:
            Tuple of (tags list, total count)
        """
        db = await self._get_db()
        
        try:
            # Build filter query
            filter_query = {}
            
            if request.category:
                filter_query["category"] = request.category
            
            if request.status:
                filter_query["status"] = request.status
            
            if request.department_id:
                filter_query["$or"] = [
                    {"department_ids": {"$size": 0}},  # Available to all departments
                    {"department_ids": ObjectId(request.department_id)}
                ]
            
            if request.parent_tag_id:
                filter_query["parent_tag_id"] = ObjectId(request.parent_tag_id)
            
            # Add search query
            if request.search:
                filter_query["$text"] = {"$search": request.search}
            
            # Build sort
            sort_field = request.sort_by
            sort_order = ASCENDING if request.sort_order == "asc" else DESCENDING
            
            # Get total count
            total = await db.tags.count_documents(filter_query)
            
            # Get tags
            cursor = db.tags.find(filter_query)
            
            if request.search:
                # Sort by text score first, then by requested field
                cursor = cursor.sort([("score", {"$meta": "textScore"}), (sort_field, sort_order)])
            else:
                cursor = cursor.sort(sort_field, sort_order)
            
            cursor = cursor.skip(request.offset).limit(request.limit)
            tags = await cursor.to_list(length=request.limit)
            
            return tags, total
            
        except Exception as e:
            logger.error(f"Error listing tags: {str(e)}")
            raise
    
    async def suggest_tags(self, request: TagSuggestRequest) -> Tuple[List[Dict[str, Any]], int]:
        """
        Suggest tags based on search query.
        
        Args:
            request: Suggestion request parameters
            
        Returns:
            Tuple of (suggested tags, total available)
        """
        db = await self._get_db()
        
        try:
            # Build filter query
            filter_query = {
                "status": TagStatus.ACTIVE,
                "name": {"$regex": request.query, "$options": "i"}
            }
            
            if request.category:
                filter_query["category"] = request.category
            
            if request.exclude_ids:
                filter_query["_id"] = {"$nin": [ObjectId(tid) for tid in request.exclude_ids]}
            
            # Get total count
            total = await db.tags.count_documents(filter_query)
            
            # Get suggestions sorted by usage count and name
            cursor = db.tags.find(
                filter_query,
                {
                    "_id": 1, "name": 1, "slug": 1, "display_name": 1,
                    "category": 1, "color": 1, "usage_count": 1
                }
            ).sort([("usage_count", DESCENDING), ("name", ASCENDING)]).limit(request.limit)
            
            tags = await cursor.to_list(length=request.limit)
            
            return tags, total
            
        except Exception as e:
            logger.error(f"Error suggesting tags: {str(e)}")
            raise
    
    async def assign_tags_to_conversation(
        self,
        conversation_id: ObjectId,
        tag_ids: List[ObjectId],
        assigned_by: ObjectId,
        auto_assigned: bool = False,
        confidence_scores: Optional[Dict[str, float]] = None
    ) -> List[Dict[str, Any]]:
        """
        Assign tags to a conversation.
        
        Args:
            conversation_id: Conversation ID
            tag_ids: List of tag IDs to assign
            assigned_by: User performing the assignment
            auto_assigned: Whether tags were auto-assigned
            confidence_scores: Confidence scores for auto-assigned tags
            
        Returns:
            List of created conversation tag documents
        """
        db = await self._get_db()
        
        try:
            # Validate conversation exists
            conversation = await db.conversations.find_one({"_id": conversation_id})
            if not conversation:
                raise ValueError("Conversation not found")
            
            # Get tags and validate they're active
            tags = await db.tags.find({
                "_id": {"$in": tag_ids},
                "status": TagStatus.ACTIVE
            }).to_list(length=len(tag_ids))
            
            if len(tags) != len(tag_ids):
                raise ValueError("One or more tags not found or inactive")
            
            # Check for existing assignments
            existing_assignments = await db.conversation_tags.find({
                "conversation_id": conversation_id,
                "tag.id": {"$in": tag_ids}
            }).to_list(length=None)
            
            existing_tag_ids = {doc["tag"]["id"] for doc in existing_assignments}
            new_tag_ids = [tid for tid in tag_ids if tid not in existing_tag_ids]
            
            if not new_tag_ids:
                return []  # All tags already assigned
            
            # Create conversation tag documents
            now = datetime.utcnow()
            conversation_tags = []
            
            for tag in tags:
                if tag["_id"] in new_tag_ids:
                    # Create denormalized tag data
                    tag_denorm = {
                        "id": tag["_id"],
                        "name": tag["name"],
                        "slug": tag["slug"],
                        "category": tag["category"],
                        "color": tag["color"],
                        "display_name": tag.get("display_name")
                    }
                    
                    # Get confidence score if provided
                    confidence = None
                    if confidence_scores and str(tag["_id"]) in confidence_scores:
                        confidence = confidence_scores[str(tag["_id"])]
                    
                    conv_tag_doc = {
                        "conversation_id": conversation_id,
                        "tag": tag_denorm,
                        "assigned_at": now,
                        "assigned_by": assigned_by,
                        "auto_assigned": auto_assigned,
                        "confidence_score": confidence,
                        "created_at": now
                    }
                    
                    conversation_tags.append(conv_tag_doc)
            
            # Insert conversation tag assignments
            if conversation_tags:
                await db.conversation_tags.insert_many(conversation_tags)
                
                # Update tag usage counts
                await db.tags.update_many(
                    {"_id": {"$in": new_tag_ids}},
                    {"$inc": {"usage_count": 1}}
                )
                
                # Update conversation with denormalized tags
                await self._update_conversation_tags_denorm(conversation_id)
            
            logger.info(f"Assigned {len(conversation_tags)} tags to conversation {conversation_id}")
            return conversation_tags
            
        except Exception as e:
            logger.error(f"Error assigning tags to conversation {conversation_id}: {str(e)}")
            raise
    
    async def unassign_tags_from_conversation(
        self,
        conversation_id: ObjectId,
        tag_ids: List[ObjectId],
        unassigned_by: ObjectId
    ) -> int:
        """
        Unassign tags from a conversation.
        
        Args:
            conversation_id: Conversation ID
            tag_ids: List of tag IDs to unassign
            unassigned_by: User performing the unassignment
            
        Returns:
            Number of tags unassigned
        """
        db = await self._get_db()
        
        try:
            # Remove conversation tag assignments
            result = await db.conversation_tags.delete_many({
                "conversation_id": conversation_id,
                "tag.id": {"$in": tag_ids}
            })
            
            if result.deleted_count > 0:
                # Update tag usage counts
                await db.tags.update_many(
                    {"_id": {"$in": tag_ids}},
                    {"$inc": {"usage_count": -1}}
                )
                
                # Ensure usage count doesn't go below 0
                await db.tags.update_many(
                    {"_id": {"$in": tag_ids}, "usage_count": {"$lt": 0}},
                    {"$set": {"usage_count": 0}}
                )
                
                # Update conversation with denormalized tags
                await self._update_conversation_tags_denorm(conversation_id)
            
            logger.info(f"Unassigned {result.deleted_count} tags from conversation {conversation_id}")
            return result.deleted_count
            
        except Exception as e:
            logger.error(f"Error unassigning tags from conversation {conversation_id}: {str(e)}")
            raise
    
    async def get_conversation_tags(self, conversation_id: ObjectId) -> List[Dict[str, Any]]:
        """Get all tags assigned to a conversation."""
        db = await self._get_db()
        
        try:
            tags = await db.conversation_tags.find({
                "conversation_id": conversation_id
            }).sort("assigned_at", ASCENDING).to_list(length=None)
            
            return tags
        except Exception as e:
            logger.error(f"Error getting conversation tags for {conversation_id}: {str(e)}")
            raise
    
    async def _update_conversation_tags_denorm(self, conversation_id: ObjectId) -> None:
        """Update denormalized tags in conversation document."""
        db = await self._get_db()
        
        try:
            # Get current conversation tags
            conv_tags = await db.conversation_tags.find({
                "conversation_id": conversation_id
            }).to_list(length=None)
            
            # Extract tag info for denormalization
            tag_data = []
            for conv_tag in conv_tags:
                tag_info = conv_tag["tag"]
                tag_data.append({
                    "id": tag_info["id"],
                    "name": tag_info["name"],
                    "slug": tag_info["slug"],
                    "category": tag_info["category"],
                    "color": tag_info["color"],
                    "display_name": tag_info.get("display_name")
                })
            
            # Update conversation
            await db.conversations.update_one(
                {"_id": conversation_id},
                {
                    "$set": {
                        "tags": tag_data,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
        except Exception as e:
            logger.error(f"Error updating conversation tags denorm for {conversation_id}: {str(e)}")
    
    async def _update_conversation_tag_denorm(self, tag_id: ObjectId, updated_tag: Dict[str, Any]) -> None:
        """Update denormalized tag data in all conversations using this tag."""
        db = await self._get_db()
        
        try:
            # Create updated denormalized tag data
            tag_denorm = {
                "id": updated_tag["_id"],
                "name": updated_tag["name"],
                "slug": updated_tag["slug"],
                "category": updated_tag["category"],
                "color": updated_tag["color"],
                "display_name": updated_tag.get("display_name")
            }
            
            # Update conversation_tags collection
            await db.conversation_tags.update_many(
                {"tag.id": tag_id},
                {"$set": {"tag": tag_denorm}}
            )
            
            # Update conversations collection denormalized data
            conversations_with_tag = await db.conversation_tags.find({
                "tag.id": tag_id
            }).distinct("conversation_id")
            
            for conv_id in conversations_with_tag:
                await self._update_conversation_tags_denorm(conv_id)
                
        except Exception as e:
            logger.error(f"Error updating denormalized tag data for tag {tag_id}: {str(e)}")


# Global tag service instance
tag_service = TagService()



