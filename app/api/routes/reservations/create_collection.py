"""Create reservations collection endpoint."""

from fastapi import APIRouter, HTTPException, status
from datetime import datetime, timezone

from app.core.logger import logger
from app.db.client import database
from app.schemas import SuccessResponse

router = APIRouter()

@router.post("/create-collection")
async def create_reservations_collection():
    """
    Create or initialize the reservations collection in MongoDB.
    This endpoint creates the collection and sets up indexes for optimal performance.
    """
    try:
        db = await database.get_database()
        
        # Check if collection already exists
        collection_names = await db.list_collection_names()
        if "installation_reservations" in collection_names:
            logger.info("Collection 'installation_reservations' already exists")
            return SuccessResponse(
                message="Reservations collection already exists",
                data={
                    "collection_name": "installation_reservations",
                    "status": "already_exists",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            )
        
        # Create the collection
        await db.create_collection("installation_reservations")
        logger.info("Created collection 'installation_reservations'")
        
        # Create indexes for better query performance
        collection = db.installation_reservations
        
        # Index on date and time_slot for quick availability queries
        await collection.create_index([("date", 1), ("time_slot", 1)], unique=True)
        
        # Index on created_at for sorting
        await collection.create_index([("created_at", -1)])
        
        # Index on customer_info.mobile_number for customer lookup
        await collection.create_index([("customer_info.mobile_number", 1)])
        
        # Index on customer_info.identification_number for customer lookup
        await collection.create_index([("customer_info.identification_number", 1)])
        
        logger.info("Created indexes for installation_reservations collection")
        
        return SuccessResponse(
            message="Reservations collection created successfully",
            data={
                "collection_name": "installation_reservations",
                "status": "created",
                "indexes_created": [
                    "date_time_slot_unique",
                    "created_at_desc",
                    "customer_mobile_number",
                    "customer_identification_number"
                ],
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )
        
    except Exception as e:
        logger.error(f"Error creating reservations collection: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create reservations collection: {str(e)}"
        )
