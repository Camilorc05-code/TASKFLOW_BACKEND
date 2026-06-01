from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from app.db.database import Base

class Team(Base):

    __tablename__ = "teams"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String, nullable=False)

    tasks = relationship("Task", back_populates="team")