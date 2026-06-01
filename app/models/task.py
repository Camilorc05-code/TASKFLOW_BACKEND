from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.db.database import Base

class Task(Base):

    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)

    title = Column(String, nullable=False)

    description = Column(String)

    status = Column(String, default="pending")

    team_id = Column(Integer, ForeignKey("teams.id"))

    owner_id = Column(Integer, ForeignKey("users.id"))

    team = relationship("Team", back_populates="tasks")