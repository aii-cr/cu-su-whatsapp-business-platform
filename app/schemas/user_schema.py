from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class Log(BaseModel):
    id: Optional[str]
    message: str
    level: str
    timestamp: datetime = datetime.utcnow()