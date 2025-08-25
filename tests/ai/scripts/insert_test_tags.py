#!/usr/bin/env python3
"""
Script to insert test tags with usage counts for testing quick add functionality.
Run this script to populate the database with sample tags.
"""

import asyncio
import sys
import os
from datetime import datetime, timezone
from bson import ObjectId

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.db.client import database
from app.core.logger import logger

# Test tags with usage counts
TEST_TAGS = [
    {"name": "Customer Support", "color": "#2563eb", "usage_count": 45, "category": "department"},
    {"name": "Billing Question", "color": "#dc2626", "usage_count": 38, "category": "billing"},
    {"name": "Technical Issue", "color": "#059669", "usage_count": 32, "category": "technical"},
    {"name": "Follow Up", "color": "#d97706", "usage_count": 28, "category": "general"},
    {"name": "Urgent", "color": "#dc2626", "usage_count": 25, "category": "priority"},
    {"name": "Feature Request", "color": "#7c3aed", "usage_count": 22, "category": "product"},
    {"name": "Bug Report", "color": "#dc2626", "usage_count": 20, "category": "technical"},
    {"name": "Account Setup", "color": "#059669", "usage_count": 18, "category": "onboarding"},
    {"name": "Payment Issue", "color": "#dc2626", "usage_count": 15, "category": "billing"},
    {"name": "General Inquiry", "color": "#6b7280", "usage_count": 12, "category": "general"},
    {"name": "Escalation", "color": "#dc2626", "usage_count": 10, "category": "priority"},
    {"name": "Resolved", "color": "#059669", "usage_count": 8, "category": "status"},
    {"name": "In Progress", "color": "#d97706", "usage_count": 6, "category": "status"},
    {"name": "Pending", "color": "#6b7280", "usage_count": 5, "category": "status"},
]

async def insert_test_tags():
    """Insert test tags into the database."""
    try:
        # Get database connection
        db = await database.get_database()
        
        # Check if tags already exist
        existing_count = await db.tags.count_documents({})
        if existing_count > 0:
            logger.info(f"Database already contains {existing_count} tags. Updating existing tags with usage counts.")
            
            # Update existing tags with usage counts
            for tag_data in TEST_TAGS:
                # Generate slug from name
                slug = tag_data["name"].lower().replace(" ", "-").replace("_", "-")
                slug = "".join(c for c in slug if c.isalnum() or c == "-")
                
                # Try to find existing tag by name
                existing_tag = await db.tags.find_one({"name": tag_data["name"]})
                if existing_tag:
                    # Update usage count
                    await db.tags.update_one(
                        {"_id": existing_tag["_id"]},
                        {"$set": {"usage_count": tag_data["usage_count"]}}
                    )
                    logger.info(f"Updated tag: {tag_data['name']} with usage_count: {tag_data['usage_count']}")
                else:
                    # Create new tag if not found
                    tag_doc = {
                        "name": tag_data["name"],
                        "slug": slug,
                        "display_name": tag_data["name"],
                        "description": f"Test tag: {tag_data['name']}",
                        "category": tag_data["category"],
                        "color": tag_data["color"],
                        "parent_tag_id": None,
                        "child_tags": [],
                        "status": "active",
                        "is_system_tag": False,
                        "is_auto_assignable": True,
                        "usage_count": tag_data["usage_count"],
                        "department_ids": [],
                        "user_ids": [],
                        "created_at": datetime.now(timezone.utc),
                        "updated_at": datetime.now(timezone.utc),
                        "created_by": ObjectId(),  # Use a dummy ObjectId
                        "updated_by": ObjectId(),  # Use a dummy ObjectId
                    }
                    
                    result = await db.tags.insert_one(tag_doc)
                    logger.info(f"Inserted new tag: {tag_data['name']} (ID: {result.inserted_id})")
            
            return
        
        logger.info("Inserting test tags...")
        
        # Insert test tags
        for tag_data in TEST_TAGS:
            # Generate slug from name
            slug = tag_data["name"].lower().replace(" ", "-").replace("_", "-")
            slug = "".join(c for c in slug if c.isalnum() or c == "-")
            
            tag_doc = {
                "name": tag_data["name"],
                "slug": slug,
                "display_name": tag_data["name"],
                "description": f"Test tag: {tag_data['name']}",
                "category": tag_data["category"],
                "color": tag_data["color"],
                "parent_tag_id": None,
                "child_tags": [],
                "status": "active",
                "is_system_tag": False,
                "is_auto_assignable": True,
                "usage_count": tag_data["usage_count"],
                "department_ids": [],
                "user_ids": [],
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc),
                "created_by": ObjectId(),  # Use a dummy ObjectId
                "updated_by": ObjectId(),  # Use a dummy ObjectId
            }
            
            result = await db.tags.insert_one(tag_doc)
            logger.info(f"Inserted tag: {tag_data['name']} (ID: {result.inserted_id})")
        
        logger.info(f"✅ Successfully inserted {len(TEST_TAGS)} test tags")
        
        # Verify insertion
        total_tags = await db.tags.count_documents({})
        logger.info(f"Total tags in database: {total_tags}")
        
        # Show top 5 by usage count
        top_tags = await db.tags.find().sort("usage_count", -1).limit(5).to_list(length=5)
        logger.info("Top 5 tags by usage count:")
        for tag in top_tags:
            logger.info(f"  - {tag['name']}: {tag['usage_count']} uses")
            
    except Exception as e:
        logger.error(f"Error inserting test tags: {str(e)}")
        raise

async def main():
    """Main function."""
    logger.info("🚀 Starting test tag insertion...")
    await insert_test_tags()
    logger.info("✅ Test tag insertion completed!")

if __name__ == "__main__":
    asyncio.run(main())
