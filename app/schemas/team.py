from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class TeamCreate(BaseModel):
    name: str
    description: Optional[str] = None

class TeamOut(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    owner_id: int
    class Config:
        from_attributes = True

class TeamMemberOut(BaseModel):
    id: int
    username: str
    email: str
    role: str
    class Config:
        from_attributes = True

class TeamInviteRequest(BaseModel):
    email: EmailStr

# ── NEW ──────────────────────────────────────────────────────────────────
class TeamInviteOut(BaseModel):
    id: int
    email: str
    team_id: int
    accepted: int          # 0=pending, 1=accepted, 2=cancelled
    created_at: Optional[datetime] = None
    class Config:
        from_attributes = True

class TeamProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None

class TeamProjectOut(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    team_id: int
    class Config:
        from_attributes = True
