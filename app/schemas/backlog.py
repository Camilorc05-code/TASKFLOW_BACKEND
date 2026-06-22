from pydantic import BaseModel
from typing import Optional
from datetime import date

class SprintCreate(BaseModel):
    name: str
    goal: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    team_id: Optional[int] = None

class SprintUpdate(BaseModel):
    name: Optional[str] = None
    goal: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    status: Optional[str] = None

class SprintOut(BaseModel):
    id: int
    name: str
    goal: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    status: str
    team_id: Optional[int] = None
    owner_id: int
    class Config:
        from_attributes = True

class BacklogItemCreate(BaseModel):
    title: str
    description: Optional[str] = None
    priority: Optional[str] = "medium"
    story_points: Optional[int] = None
    sprint_id: Optional[int] = None
    team_id: Optional[int] = None
    assignee_id: Optional[int] = None
    labels: Optional[str] = None
    item_type: Optional[str] = "story"

class BacklogItemUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[str] = None
    story_points: Optional[int] = None
    sprint_id: Optional[int] = None
    assignee_id: Optional[int] = None
    labels: Optional[str] = None
    item_type: Optional[str] = None
    status: Optional[str] = None

class BacklogItemOut(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    priority: str
    story_points: Optional[int] = None
    sprint_id: Optional[int] = None
    team_id: Optional[int] = None
    assignee_id: Optional[int] = None
    labels: Optional[str] = None
    item_type: str
    status: str
    owner_id: int
    class Config:
        from_attributes = True

class MoveToSprintRequest(BaseModel):
    sprint_id: Optional[int] = None
