"""Participant schemas for conversations."""

from enum import Enum
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
from app.db.models.base import PyObjectId


class ParticipantRole(str, Enum):
    primary = "primary"
    agent = "agent"
    observer = "observer"


class ParticipantIn(BaseModel):
    user_id: PyObjectId = Field(..., description="User ID")
    role: ParticipantRole = Field(..., description="Participant role")


class ParticipantOut(BaseModel):
    id: PyObjectId = Field(alias="_id")
    user_id: PyObjectId
    role: ParticipantRole
    added_at: datetime
    removed_at: Optional[datetime] = None

    class Config:
        populate_by_name = True


class ParticipantEvent(BaseModel):
    type: str = Field(..., description="Event type: added|removed|role_changed")
    ts_utc: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    actor_id: Optional[PyObjectId] = None
    payload: Dict[str, Any] = Field(default_factory=dict)


class ParticipantListResponse(BaseModel):
    items: List[ParticipantOut]
    conversation_id: PyObjectId


