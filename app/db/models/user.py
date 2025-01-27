from pydantic import BaseModel, EmailStr
from typing import Optional

class User(BaseModel):
    id: str
    name: str
    email: Optional[EmailStr]
    phone_number: Optional[str]
    role: str 
    status: str
