from typing import Optional
from pydantic import BaseModel
from datetime import date

class TaskCreate(BaseModel):
    title: str
    description: str
    status: Optional[str] = "todo"
    priority: Optional[str] = "medium"
    due_date: Optional[date] = None
    team_id: Optional[int] = None   # ⚡ opcional


