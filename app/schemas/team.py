from pydantic import BaseModel, EmailStr
from typing import Optional

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

class TeamProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None
    team_id: int

class TeamProjectOut(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    team_id: int
    class Config:
        from_attributes = True
