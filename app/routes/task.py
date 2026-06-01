from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.schemas.task import TaskCreate
from app.models.task import Task
from app.db.dependencies import get_db

router = APIRouter(prefix="/tasks")

@router.post("/")
def create_task(
    task: TaskCreate,
    db: Session = Depends(get_db)
):

    new_task = Task(
        title=task.title,
        description=task.description,
        team_id=task.team_id
    )

    db.add(new_task)

    db.commit()

    db.refresh(new_task)

    return new_task