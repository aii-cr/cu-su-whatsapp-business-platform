"""Book installation reservation endpoint."""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field, field_validator
from datetime import datetime, timezone
from typing import Optional
import re

from app.core.logger import logger
from app.db.client import database
from app.schemas import SuccessResponse

router = APIRouter()

class CustomerInfo(BaseModel):
    """Customer information for the reservation."""
    full_name: str = Field(..., min_length=2, max_length=100, description="Customer full name")
    identification_number: str = Field(..., min_length=5, max_length=50, description="Customer identification number (ID, passport, etc.)")
    email: str = Field(..., description="Valid customer email address")
    mobile_number: str = Field(..., description="Customer mobile phone number")

    @field_validator('mobile_number')
    @classmethod
    def validate_mobile_number(cls, v: str) -> str:
        # Remove any spaces, dashes, or parentheses
        phone = re.sub(r'[\s\-\(\)]', '', v)
        
        # Check if it's a valid phone number (8-15 digits)
        if not re.match(r'^\+?[\d]{8,15}$', phone):
            raise ValueError('Invalid mobile number format')
        
        return phone

    @field_validator('email')
    @classmethod
    def validate_email(cls, v: str) -> str:
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_regex, v.strip()):
            raise ValueError('Invalid email format')
        return v.strip().lower()

    @field_validator('identification_number')
    @classmethod
    def validate_identification_number(cls, v: str) -> str:
        # Remove spaces and validate format
        id_number = re.sub(r'\s+', '', v)
        
        # Basic validation: alphanumeric characters only
        if not re.match(r'^[A-Za-z0-9\-]+$', id_number):
            raise ValueError('Identification number must contain only letters, numbers, and hyphens')
        
        return id_number.upper()

class ReservationRequest(BaseModel):
    """Request model for booking a reservation."""
    date: str = Field(..., description="Reservation date in YYYY-MM-DD format")
    time_slot: str = Field(..., description="Time slot (08:00 or 13:00)")
    customer_info: CustomerInfo = Field(..., description="Customer information")
    service_type: Optional[str] = Field(default="fiber_installation", description="Type of installation service")

    @field_validator('date')
    @classmethod
    def validate_date(cls, v: str) -> str:
        try:
            # Parse and validate date format
            parsed_date = datetime.strptime(v, "%Y-%m-%d")
            
            # Check if date is not in the past
            today = datetime.now().date()
            if parsed_date.date() < today:
                raise ValueError('Cannot book reservations for past dates')
            
            return v
        except ValueError as e:
            if "time data" in str(e):
                raise ValueError('Date must be in YYYY-MM-DD format')
            raise e

    @field_validator('time_slot')
    @classmethod
    def validate_time_slot(cls, v: str) -> str:
        valid_slots = ["08:00", "13:00"]
        if v not in valid_slots:
            raise ValueError(f'Time slot must be one of: {", ".join(valid_slots)}')
        return v

@router.post("/book")
async def book_reservation(reservation: ReservationRequest):
    """
    Book an installation reservation slot.
    
    This endpoint allows customers to book available installation slots.
    It will check if the requested slot is available and save the reservation to MongoDB.
    
    Request Body:
    - date: Reservation date in YYYY-MM-DD format
    - time_slot: Time slot (08:00 or 13:00)
    - customer_info: Required customer details
      - full_name: Customer's complete name
      - identification_number: ID number, passport, or similar
      - email: Valid email address
      - mobile_number: Mobile phone number
    - service_type: Type of installation (defaults to "fiber_installation")
    
    Returns:
    - Success response with reservation details and confirmation ID
    """
    try:
        db = await database.get_database()
        
        # Check if the slot is already booked
        existing_reservation = await db.installation_reservations.find_one({
            "date": reservation.date,
            "time_slot": reservation.time_slot
        })
        
        if existing_reservation:
            logger.warning(f"Slot already booked: {reservation.date} at {reservation.time_slot}")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"The requested slot ({reservation.date} at {reservation.time_slot}) is already booked"
            )
        
        # Prepare reservation document
        reservation_doc = {
            "date": reservation.date,
            "time_slot": reservation.time_slot,
            "customer_info": {
                "full_name": reservation.customer_info.full_name,
                "identification_number": reservation.customer_info.identification_number,
                "email": reservation.customer_info.email,
                "mobile_number": reservation.customer_info.mobile_number
            },
            "service_type": reservation.service_type,
            "status": "confirmed",
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }
        
        # Insert the reservation
        result = await db.installation_reservations.insert_one(reservation_doc)
        
        if not result.inserted_id:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create reservation"
            )
        
        reservation_id = str(result.inserted_id)
        
        logger.info(f"Reservation created successfully: {reservation_id} for {reservation.date} at {reservation.time_slot}")
        logger.info(f"Customer: {reservation.customer_info.full_name} (ID: {reservation.customer_info.identification_number}, Mobile: {reservation.customer_info.mobile_number})")
        
        return SuccessResponse(
            message="Reservation booked successfully",
            data={
                "reservation_id": reservation_id,
                "confirmation_number": f"INS-{reservation.date.replace('-', '')}-{reservation.time_slot.replace(':', '')}-{reservation_id[-6:].upper()}",
                "date": reservation.date,
                "time_slot": reservation.time_slot,
                "customer_info": {
                    "full_name": reservation.customer_info.full_name,
                    "identification_number": reservation.customer_info.identification_number,
                    "email": reservation.customer_info.email,
                    "mobile_number": reservation.customer_info.mobile_number
                },
                "service_type": reservation.service_type,
                "status": "confirmed",
                "created_at": datetime.now(timezone.utc).isoformat()
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error booking reservation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to book reservation: {str(e)}"
        )
