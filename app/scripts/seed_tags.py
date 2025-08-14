#!/usr/bin/env python3
"""
Seed script to create initial tags for the WhatsApp Business Platform.
This script creates a variety of tags across different categories for testing.
"""

import asyncio
import sys
import os
from datetime import datetime, timezone
from bson import ObjectId

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.client import database
from app.services.whatsapp.tag_service import tag_service
from app.schemas.whatsapp.chat.tag import TagCreate, TagCategory
from app.core.logger import logger

# Initial tags data
INITIAL_TAGS = [
    # Priority tags
    {
        "name": "High Priority",
        "color": "#dc2626",  # red-600
        "category": TagCategory.PRIORITY,
        "description": "Urgent issues requiring immediate attention"
    },
    {
        "name": "Medium Priority", 
        "color": "#d97706",  # amber-600
        "category": TagCategory.PRIORITY,
        "description": "Important issues that need attention soon"
    },
    {
        "name": "Low Priority",
        "color": "#059669",  # emerald-600
        "category": TagCategory.PRIORITY,
        "description": "Non-urgent issues that can be addressed later"
    },
    
    # Issue type tags
    {
        "name": "Technical Support",
        "color": "#2563eb",  # blue-600
        "category": TagCategory.ISSUE_TYPE,
        "description": "Technical issues and troubleshooting"
    },
    {
        "name": "Billing Question",
        "color": "#7c3aed",  # violet-600
        "category": TagCategory.ISSUE_TYPE,
        "description": "Questions about billing and payments"
    },
    {
        "name": "Feature Request",
        "color": "#0d9488",  # teal-600
        "category": TagCategory.ISSUE_TYPE,
        "description": "Requests for new features or improvements"
    },
    {
        "name": "Bug Report",
        "color": "#dc2626",  # red-600
        "category": TagCategory.ISSUE_TYPE,
        "description": "Reports of software bugs or issues"
    },
    
    # Customer type tags
    {
        "name": "New Customer",
        "color": "#16a34a",  # green-600
        "category": TagCategory.CUSTOMER_TYPE,
        "description": "First-time customers"
    },
    {
        "name": "Returning Customer",
        "color": "#059669",  # emerald-600
        "category": TagCategory.CUSTOMER_TYPE,
        "description": "Existing customers with previous interactions"
    },
    {
        "name": "VIP Customer",
        "color": "#9333ea",  # purple-600
        "category": TagCategory.CUSTOMER_TYPE,
        "description": "High-value customers requiring special attention"
    },
    
    # Status tags
    {
        "name": "In Progress",
        "color": "#d97706",  # amber-600
        "category": TagCategory.STATUS,
        "description": "Issue is being worked on"
    },
    {
        "name": "Resolved",
        "color": "#059669",  # emerald-600
        "category": TagCategory.STATUS,
        "description": "Issue has been resolved"
    },
    {
        "name": "Escalated",
        "color": "#dc2626",  # red-600
        "category": TagCategory.STATUS,
        "description": "Issue has been escalated to higher level"
    },
    {
        "name": "Pending Customer",
        "color": "#6b7280",  # gray-500
        "category": TagCategory.STATUS,
        "description": "Waiting for customer response"
    },
    
    # Product tags
    {
        "name": "Mobile App",
        "color": "#2563eb",  # blue-600
        "category": TagCategory.PRODUCT,
        "description": "Issues related to mobile application"
    },
    {
        "name": "Web Platform",
        "color": "#4f46e5",  # indigo-600
        "category": TagCategory.PRODUCT,
        "description": "Issues related to web platform"
    },
    {
        "name": "API Integration",
        "color": "#0d9488",  # teal-600
        "category": TagCategory.PRODUCT,
        "description": "Issues related to API integrations"
    },
    
    # General tags
    {
        "name": "Urgent",
        "color": "#dc2626",  # red-600
        "category": TagCategory.GENERAL,
        "description": "Requires immediate attention"
    },
    {
        "name": "Follow Up",
        "color": "#d97706",  # amber-600
        "category": TagCategory.GENERAL,
        "description": "Needs follow up action"
    },
    {
        "name": "Documentation",
        "color": "#6b7280",  # gray-500
        "category": TagCategory.GENERAL,
        "description": "Related to documentation or guides"
    },
    {
        "name": "Training",
        "color": "#0d9488",  # teal-600
        "category": TagCategory.GENERAL,
        "description": "Training or onboarding related"
    }
]

async def seed_tags():
    """Seed the database with initial tags."""
    try:
        # Connect to database
        await database.connect()
        logger.info("Connected to database")
        
        # Create a system user ID for seeding
        system_user_id = ObjectId()
        
        created_count = 0
        skipped_count = 0
        
        for tag_data in INITIAL_TAGS:
            try:
                # Create tag using service
                tag_create = TagCreate(
                    name=tag_data["name"],
                    color=tag_data["color"],
                    category=tag_data["category"],
                    description=tag_data["description"]
                )
                
                created_tag = await tag_service.create_tag(tag_create, system_user_id)
                created_count += 1
                logger.info(f"✅ Created tag: {tag_data['name']} (ID: {created_tag['_id']})")
                
            except ValueError as e:
                if "already exists" in str(e):
                    skipped_count += 1
                    logger.info(f"⏭️ Skipped existing tag: {tag_data['name']}")
                else:
                    logger.error(f"❌ Error creating tag {tag_data['name']}: {str(e)}")
            except Exception as e:
                logger.error(f"❌ Unexpected error creating tag {tag_data['name']}: {str(e)}")
        
        logger.info(f"🎉 Seeding complete! Created: {created_count}, Skipped: {skipped_count}")
        
        # Verify tags were created
        db = await database._get_db()
        total_tags = await db.tags.count_documents({"status": "active"})
        logger.info(f"📊 Total active tags in database: {total_tags}")
        
    except Exception as e:
        logger.error(f"❌ Error during seeding: {str(e)}")
        raise
    finally:
        await database.disconnect()
        logger.info("Disconnected from database")

if __name__ == "__main__":
    asyncio.run(seed_tags())
