from sqlalchemy import Column, Integer, String, Text, Date, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime

from app.db.database import Base          

class Sprint(Base):
    __tablename__ = "sprints"

    id         = Column(Integer, primary_key=True, index=True)
    name       = Column(String, nullable=False)
    goal       = Column(Text, nullable=True)
    start_date = Column(Date, nullable=True)
    end_date   = Column(Date, nullable=True)
    status     = Column(String, default="planning")  # planning | active | completed
    team_id    = Column(Integer, ForeignKey("teams.id", ondelete="SET NULL"), nullable=True)
    owner_id   = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    items = relationship("BacklogItem", back_populates="sprint", lazy="dynamic")


class BacklogItem(Base):
    __tablename__ = "backlog_items"

    id           = Column(Integer, primary_key=True, index=True)
    title        = Column(String, nullable=False)
    description  = Column(Text, nullable=True)
    priority     = Column(String, default="medium")     
    story_points = Column(Integer, nullable=True)
    sprint_id    = Column(Integer, ForeignKey("sprints.id", ondelete="SET NULL"), nullable=True)
    team_id      = Column(Integer, ForeignKey("teams.id",   ondelete="SET NULL"), nullable=True)
    assignee_id  = Column(Integer, ForeignKey("users.id",   ondelete="SET NULL"), nullable=True)
    owner_id     = Column(Integer, ForeignKey("users.id",   ondelete="CASCADE"), nullable=False)
    labels       = Column(String, nullable=True)         
    item_type    = Column(String, default="story")       
    status       = Column(String, default="backlog")    
    created_at   = Column(DateTime, default=datetime.utcnow)

    sprint = relationship("Sprint", back_populates="items")
