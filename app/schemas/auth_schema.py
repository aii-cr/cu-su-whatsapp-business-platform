from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class RegisterSchema(BaseModel):
    email: str
    password: str
    role: Optional[str]
    full_name: str
    phone: Optional[str]
    mobile: Optional[str]

class LoginSchema(BaseModel):
    username: str
    password: str
