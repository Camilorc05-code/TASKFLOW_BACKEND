from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.schemas.task import TaskCreate
from app.models.task import Task
from app.db.dependencies import get_db
from app.auth.dependencies import get_current_user
from app.models.user import User

router = APIRouter(prefix="/tasks")

@router.post("/")
def create_task(
    task: TaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    new_task = Task(
        title=task.title,
        description=task.description,
        team_id=task.team_id,
        owner_id=current_user.id
    )

    db.add(new_task)

    db.commit()

    db.refresh(new_task)

    return new_task