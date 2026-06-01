from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.schemas.team import TeamCreate
from app.models.team import Team
from app.db.dependencies import get_db

router = APIRouter(prefix="/teams")

@router.post("/")
def create_team(
    team: TeamCreate,
    db: Session = Depends(get_db)
):

    new_team = Team(name=team.name)

    db.add(new_team)

    db.commit()

    db.refresh(new_team)

    return new_team