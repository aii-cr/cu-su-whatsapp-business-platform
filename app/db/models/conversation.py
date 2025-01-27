from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional

class Conversation(BaseModel):
    id: str
    customer_id: str
    agent_id: Optional[str]  # Null if no agent assigned
    status: str  # "active", "resolved"
    tags: Optional[List[str]]
    created_at: datetime
    updated_at: datetime
