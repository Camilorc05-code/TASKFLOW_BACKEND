from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.schemas.team import (
TeamCreate, TeamOut, TeamMemberOut,
TeamInviteRequest, TeamProjectCreate, TeamProjectOut
)
from app.models.team_member import Team, TeamMember, TeamInvite, TeamProject
from app.db.dependencies import get_db
from app.auth.dependencies import get_current_user
from app.models.user import User
import secrets


router = APIRouter(prefix="/teams", tags=["teams"])

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

@router.get("/")
def get_teams(
    db: Session = Depends(get_db)
):
    teams = db.query(Team).all()
    return teams

# ── Create team ─────────────────────────────────────────────────────────────
@router.post("/", response_model=TeamOut, status_code=201)
def create_team(data: TeamCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    team = Team(name=data.name, description=data.description, owner_id=current_user.id)
    db.add(team)
    db.flush()
    # Auto-add owner as member
    member = TeamMember(team_id=team.id, user_id=current_user.id, role="owner")
    db.add(member)
    db.commit()
    db.refresh(team)
    return team


# ── List my teams ────────────────────────────────────────────────────────────
@router.get("/", response_model=list[TeamOut])
def list_teams(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    memberships = db.query(TeamMember).filter(TeamMember.user_id == current_user.id).all()
    team_ids = [m.team_id for m in memberships]
    return db.query(Team).filter(Team.id.in_(team_ids)).all()


# ── Get team details ─────────────────────────────────────────────────────────
@router.get("/{team_id}", response_model=TeamOut)
def get_team(team_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(404, "Team not found")
    _assert_member(db, team_id, current_user.id)
    return team


# ── List team members ────────────────────────────────────────────────────────
@router.get("/{team_id}/members", response_model=list[TeamMemberOut])
def list_members(team_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _assert_member(db, team_id, current_user.id)
    rows = db.query(TeamMember, User).join(User, User.id == TeamMember.user_id).filter(TeamMember.team_id == team_id).all()
    return [TeamMemberOut(id=u.id, username=u.username, email=u.email, role=m.role) for m, u in rows]


# ── Invite user by email ─────────────────────────────────────────────────────
@router.post("/{team_id}/invite", status_code=200)
def invite_member(team_id: int, data: TeamInviteRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(404, "Team not found")
    if team.owner_id != current_user.id:
        raise HTTPException(403, "Only the team owner can invite members")

    token = secrets.token_urlsafe(32)
    invite = TeamInvite(team_id=team_id, email=data.email, token=token)
    db.add(invite)
    db.commit()

    # In production: send email with invite link containing token
    return {
        "message": f"Invitation sent to {data.email}",
        "invite_token": token,       # REMOVE in production
        "team_name": team.name,
        "dev_note": "In production this token is sent by email"
    }


# ── Accept invite ─────────────────────────────────────────────────────────────
@router.post("/invites/accept", status_code=200)
def accept_invite(token: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    invite = db.query(TeamInvite).filter(TeamInvite.token == token, TeamInvite.accepted == 0).first()
    if not invite:
        raise HTTPException(400, "Invalid or already used invite token")

    # Check user email matches invite
    if current_user.email != invite.email:
        raise HTTPException(403, "This invite was sent to a different email address")

    # Check already a member
    existing = db.query(TeamMember).filter(TeamMember.team_id == invite.team_id, TeamMember.user_id == current_user.id).first()
    if existing:
        raise HTTPException(400, "You are already a member of this team")

    member = TeamMember(team_id=invite.team_id, user_id=current_user.id, role="member")
    db.add(member)
    invite.accepted = 1
    db.commit()
    return {"message": "You have joined the team!", "team_id": invite.team_id}


# ── Remove member ─────────────────────────────────────────────────────────────
@router.delete("/{team_id}/members/{user_id}", status_code=204)
def remove_member(team_id: int, user_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(404, "Team not found")
    if team.owner_id != current_user.id and current_user.id != user_id:
        raise HTTPException(403, "Not authorized")
    member = db.query(TeamMember).filter(TeamMember.team_id == team_id, TeamMember.user_id == user_id).first()
    if member:
        db.delete(member)
        db.commit()


# ── Team Projects ─────────────────────────────────────────────────────────────
@router.post("/{team_id}/projects", response_model=TeamProjectOut, status_code=201)
def create_project(team_id: int, data: TeamProjectCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _assert_member(db, team_id, current_user.id)
    project = TeamProject(name=data.name, description=data.description, team_id=team_id)
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


@router.get("/{team_id}/projects", response_model=list[TeamProjectOut])
def list_projects(team_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _assert_member(db, team_id, current_user.id)
    return db.query(TeamProject).filter(TeamProject.team_id == team_id).all()


# ── Helper ────────────────────────────────────────────────────────────────────
def _assert_member(db, team_id, user_id):
    m = db.query(TeamMember).filter(TeamMember.team_id == team_id, TeamMember.user_id == user_id).first()
    if not m:
        raise HTTPException(403, "You are not a member of this team")
