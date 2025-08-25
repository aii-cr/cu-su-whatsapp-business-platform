# NEW CODE
"""
Pydantic contract schemas (for future persistence/serialization).
"""

from __future__ import annotations
from typing import Optional
from pydantic import BaseModel, EmailStr, Field

class Selection(BaseModel):
    plan_id: int
    plan_name: str
    base_price_crc: int
    iptv_count: int = Field(ge=0, le=10)
    telefonia: bool
    extras_price_crc: int
    total_price_crc: int

class Customer(BaseModel):
    full_name: str
    identification_number: str
    email: EmailStr
    mobile_number: str

class Booking(BaseModel):
    date: str
    time_slot: str
    reservation_id: Optional[str] = None
    confirmation_number: Optional[str] = None
