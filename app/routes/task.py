from fastapi import APIRouter, Depends, Query
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

@router.get("/")
def get_tasks(
    status: str = Query(None),
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    query = db.query(Task).filter(
        Task.owner_id == current_user.id
    )

    if status:
        query = query.filter(Task.status == status)

    tasks = query.offset(skip).limit(limit).all()

    return tasks

@router.get("/{task_id}")
def get_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    task = db.query(Task).filter(
        Task.id == task_id,
        Task.owner_id == current_user.id
    ).first()

    if not task:
        return {"error": "Task not found"}

    return task

@router.put("/{task_id}")
def update_task(
    task_id: int,
    updated_task: TaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    task = db.query(Task).filter(
        Task.id == task_id,
        Task.owner_id == current_user.id
    ).first()

    if not task:
        return {"error": "Task not found"}

    task.title = updated_task.title
    task.description = updated_task.description
    task.team_id = updated_task.team_id

    db.commit()

    return {
        "message": "Task updated"
    }

@router.delete("/{task_id}")
def delete_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    task = db.query(Task).filter(
        Task.id == task_id,
        Task.owner_id == current_user.id
    ).first()

    if not task:
        return {"error": "Task not found"}

    db.delete(task)

    db.commit()

    return {
        "message": "Task deleted"
    }