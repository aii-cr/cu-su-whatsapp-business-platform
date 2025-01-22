from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class UserModel(BaseModel):
    id: Optional[str]
    username: str
    hashed_password: str
    role: Optional[str]
    full_name: Optional[str]
    id_card: Optional[str]
    Properties: Optional[List[str]]
    Condos: Optional[List[str]]
    type: Optional[str]
    phone: Optional[str] = None
    mobile: Optional[str]
    photo: Optional[str]
    email: Optional[str]
    is_active: bool = True
    created_at: datetime = datetime.utcnow()
    created_by: Optional[str] = None
    deleted_at: Optional[datetime] = None
    deleted_by: Optional[str] = None
    last_update_at: datetime = datetime.utcnow()
