from typing import Optional
from pydantic import BaseModel
from datetime import date

class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    status: Optional[str] = "todo"
    priority: Optional[str] = "medium"
    team_id: Optional[int] = None
    project_id: Optional[int] = None
    assigned_to: Optional[int] = None
    due_date: Optional[date] = None

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    team_id: Optional[int] = None
    project_id: Optional[int] = None
    assigned_to: Optional[int] = None
    due_date: Optional[date] = None

class TaskOut(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    status: str
    priority: str
    team_id: Optional[int] = None
    project_id: Optional[int] = None
    assigned_to: Optional[int] = None
    owner_id: int
    due_date: Optional[date] = None
    class Config:
        from_attributes = True

