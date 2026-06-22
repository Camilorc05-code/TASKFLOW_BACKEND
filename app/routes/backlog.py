from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional

from app.db.dependencies import get_db
from app.auth.dependencies import get_current_user
from app.models.user import User
from app.models.backlog import Sprint, BacklogItem
from app.schemas.backlog import (
    SprintCreate, SprintUpdate, SprintOut,
    BacklogItemCreate, BacklogItemUpdate, BacklogItemOut,
    MoveToSprintRequest,
)

router = APIRouter(prefix="/backlog", tags=["backlog"])


# ════════════════════════════════════════════════════════════
#  SPRINTS
# ════════════════════════════════════════════════════════════

@router.post("/sprints", response_model=SprintOut, status_code=201)
def create_sprint(
    data: SprintCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    sprint = Sprint(**data.model_dump(), owner_id=current_user.id)
    db.add(sprint)
    db.commit()
    db.refresh(sprint)
    return sprint


@router.get("/sprints", response_model=List[SprintOut])
def list_sprints(
    team_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = db.query(Sprint).filter(Sprint.owner_id == current_user.id)
    if team_id:
        q = q.filter(Sprint.team_id == team_id)
    return q.order_by(Sprint.created_at.desc()).all()


@router.get("/sprints/{sprint_id}", response_model=SprintOut)
def get_sprint(
    sprint_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    sprint = db.query(Sprint).filter(Sprint.id == sprint_id).first()
    if not sprint:
        raise HTTPException(404, "Sprint not found")
    return sprint


@router.put("/sprints/{sprint_id}", response_model=SprintOut)
def update_sprint(
    sprint_id: int,
    data: SprintUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    sprint = db.query(Sprint).filter(Sprint.id == sprint_id, Sprint.owner_id == current_user.id).first()
    if not sprint:
        raise HTTPException(404, "Sprint not found")
    for k, v in data.model_dump(exclude_none=True).items():
        setattr(sprint, k, v)
    db.commit()
    db.refresh(sprint)
    return sprint


@router.delete("/sprints/{sprint_id}", status_code=204)
def delete_sprint(
    sprint_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    sprint = db.query(Sprint).filter(Sprint.id == sprint_id, Sprint.owner_id == current_user.id).first()
    if not sprint:
        raise HTTPException(404, "Sprint not found")
    # Move items back to backlog before deleting sprint
    db.query(BacklogItem).filter(BacklogItem.sprint_id == sprint_id).update({"sprint_id": None, "status": "backlog"})
    db.delete(sprint)
    db.commit()


# ════════════════════════════════════════════════════════════
#  BACKLOG ITEMS
# ════════════════════════════════════════════════════════════

@router.post("/items", response_model=BacklogItemOut, status_code=201)
def create_item(
    data: BacklogItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    item = BacklogItem(**data.model_dump(), owner_id=current_user.id)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.get("/items", response_model=List[BacklogItemOut])
def list_items(
    sprint_id: Optional[int] = None,
    team_id:   Optional[int] = None,
    unassigned_sprint: bool = False,   # True = only items with no sprint (pure backlog)
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = db.query(BacklogItem).filter(BacklogItem.owner_id == current_user.id)
    if unassigned_sprint:
        q = q.filter(BacklogItem.sprint_id == None)
    elif sprint_id is not None:
        q = q.filter(BacklogItem.sprint_id == sprint_id)
    if team_id:
        q = q.filter(BacklogItem.team_id == team_id)
    return q.order_by(BacklogItem.created_at.desc()).all()


@router.get("/items/{item_id}", response_model=BacklogItemOut)
def get_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    item = db.query(BacklogItem).filter(BacklogItem.id == item_id).first()
    if not item:
        raise HTTPException(404, "Item not found")
    return item


@router.put("/items/{item_id}", response_model=BacklogItemOut)
def update_item(
    item_id: int,
    data: BacklogItemUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    item = db.query(BacklogItem).filter(BacklogItem.id == item_id, BacklogItem.owner_id == current_user.id).first()
    if not item:
        raise HTTPException(404, "Item not found")
    for k, v in data.model_dump(exclude_none=True).items():
        setattr(item, k, v)
    db.commit()
    db.refresh(item)
    return item


@router.patch("/items/{item_id}/move", response_model=BacklogItemOut)
def move_item_to_sprint(
    item_id: int,
    data: MoveToSprintRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Move a backlog item into a sprint (or back to backlog if sprint_id=None)."""
    item = db.query(BacklogItem).filter(BacklogItem.id == item_id, BacklogItem.owner_id == current_user.id).first()
    if not item:
        raise HTTPException(404, "Item not found")
    item.sprint_id = data.sprint_id
    item.status    = "backlog" if data.sprint_id is None else "todo"
    db.commit()
    db.refresh(item)
    return item


@router.delete("/items/{item_id}", status_code=204)
def delete_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    item = db.query(BacklogItem).filter(BacklogItem.id == item_id, BacklogItem.owner_id == current_user.id).first()
    if not item:
        raise HTTPException(404, "Item not found")
    db.delete(item)
    db.commit()


# ════════════════════════════════════════════════════════════
#  CALENDAR  — tasks + backlog items with due dates
# ════════════════════════════════════════════════════════════

@router.get("/calendar")
def get_calendar_events(
    year:  int,
    month: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Returns all events for a given month:
      - Backlog items with due dates (via end_date on sprint or item created_at)
      - Sprints overlapping the month
      - Regular tasks with due_date (from existing tasks table)
    """
    from datetime import date as dt
    import calendar as cal

    first_day = dt(year, month, 1)
    last_day  = dt(year, month, cal.monthrange(year, month)[1])

    # Sprints overlapping this month
    sprints = db.query(Sprint).filter(
        Sprint.owner_id == current_user.id,
        Sprint.start_date <= last_day,
        Sprint.end_date   >= first_day,
    ).all()

    sprint_events = [
        {
            "id":    f"sprint-{s.id}",
            "type":  "sprint",
            "title": s.name,
            "start": str(s.start_date),
            "end":   str(s.end_date),
            "status": s.status,
            "goal":  s.goal,
        }
        for s in sprints if s.start_date and s.end_date
    ]

    # Try to pull tasks with due_date (uses existing Task model — adjust import)
    task_events = []
    try:
        from app.models.task import Task   # adjust if your model is named differently
        tasks = db.query(Task).filter(
            Task.owner_id == current_user.id,
            Task.due_date >= first_day,
            Task.due_date <= last_day,
        ).all()
        task_events = [
            {
                "id":       f"task-{t.id}",
                "type":     "task",
                "title":    t.title,
                "date":     str(t.due_date),
                "status":   t.status,
                "priority": t.priority,
            }
            for t in tasks
        ]
    except Exception:
        pass   # Task model path may differ — safe to skip

    # Backlog items that belong to a sprint ending this month
    backlog_events = []
    for s in sprints:
        items = db.query(BacklogItem).filter(BacklogItem.sprint_id == s.id).all()
        for item in items:
            backlog_events.append({
                "id":           f"backlog-{item.id}",
                "type":         "backlog_item",
                "title":        item.title,
                "date":         str(s.end_date) if s.end_date else None,
                "sprint_id":    s.id,
                "sprint_name":  s.name,
                "priority":     item.priority,
                "item_type":    item.item_type,
                "story_points": item.story_points,
                "status":       item.status,
            })

    return {
        "year":   year,
        "month":  month,
        "events": sprint_events + task_events + backlog_events,
    }
