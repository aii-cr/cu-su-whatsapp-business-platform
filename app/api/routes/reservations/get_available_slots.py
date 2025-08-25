"""Get available installation slots endpoint."""

from fastapi import APIRouter, HTTPException, status, Query
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

from app.core.logger import logger
from app.db.client import database

router = APIRouter()

@router.get("/available-slots")
async def get_available_slots():
    """
    Get available installation slots for the next month starting from tomorrow.
    
    Returns available time slots for each day from tomorrow to one month in the future,
    excluding slots that are already booked and past dates.
    Available slots are 08:00 and 13:00 every day.
    If both slots for a day are taken, that day won't appear in the response.
    
    Returns:
    - available_slots: Dictionary with dates as keys and available time slots as values
    - period: Information about the date range
    - total_days_available: Number of days with available slots
    - total_slots_available: Total number of available slots
    """
    try:
        # Calculate date range: from tomorrow to one month in the future
        now = datetime.now(timezone.utc)
        tomorrow = now + timedelta(days=1)
        start_date = tomorrow.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = start_date + timedelta(days=30)  # One month from tomorrow
        
        logger.info(f"Getting available slots from {start_date.date()} to {end_date.date()}")
        
        # Get database connection
        db = await database.get_database()
        
        # Query all booked slots for the date range
        booked_slots = await db.installation_reservations.find(
            {
                "date": {
                    "$gte": start_date.strftime("%Y-%m-%d"),
                    "$lte": end_date.strftime("%Y-%m-%d")
                }
            },
            {"date": 1, "time_slot": 1}
        ).to_list(length=None)
        
        logger.info(f"Found {len(booked_slots)} booked slots in the date range")
        
        # Create a set of booked date-time combinations for quick lookup
        booked_datetime_set = set()
        for slot in booked_slots:
            booked_datetime_set.add(f"{slot['date']}_{slot['time_slot']}")
        
        # Generate all possible slots for the month
        available_slots = {}
        current_date = start_date
        
        # Define available time slots
        time_slots = ["08:00", "13:00"]
        
        while current_date <= end_date:
            date_str = current_date.strftime("%Y-%m-%d")
            day_available_slots = []
            
            # Check each time slot for this date
            for time_slot in time_slots:
                datetime_key = f"{date_str}_{time_slot}"
                if datetime_key not in booked_datetime_set:
                    day_available_slots.append(time_slot)
            
            # Only include the date if there are available slots
            if day_available_slots:
                available_slots[date_str] = day_available_slots
            
            # Move to next day
            current_date += timedelta(days=1)
        
        logger.info(f"Generated {len(available_slots)} days with available slots")
        
        return {
            "available_slots": available_slots,
            "period": {
                "start_date": start_date.strftime("%Y-%m-%d"),
                "end_date": end_date.strftime("%Y-%m-%d"),
                "total_days": 31,
                "description": f"From tomorrow ({start_date.strftime('%Y-%m-%d')}) to one month in the future"
            },
            "total_days_available": len(available_slots),
            "total_slots_available": sum(len(slots) for slots in available_slots.values())
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting available slots: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get available slots: {str(e)}"
        )
