from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import secrets

from app.db.dependencies import get_db
from app.auth.dependencies import get_current_user
from app.models.user import User
from app.models.team_member import Team
from app.models.team_member import TeamMember, TeamInvite, TeamProject
from app.schemas.team import (
    TeamCreate, TeamOut, TeamMemberOut,
    TeamInviteRequest, TeamInviteOut,
    TeamProjectCreate, TeamProjectOut,
)
from app.utils.email_service import send_team_invite_email

router = APIRouter(prefix="/teams", tags=["teams"])


# ── helpers ───────────────────────────────────────────────────────────────
def _get_team_or_404(db, team_id):
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(404, "Team not found")
    return team

def _assert_owner(team, current_user):
    if team.owner_id != current_user.id:
        raise HTTPException(403, "Only the team owner can perform this action")

def _assert_member(db, team_id, user_id):
    m = db.query(TeamMember).filter(
        TeamMember.team_id == team_id,
        TeamMember.user_id == user_id,
    ).first()
    if not m:
        raise HTTPException(403, "You are not a member of this team")


# ════════════════════════════════════════════════
#  TEAM CRUD
# ════════════════════════════════════════════════

@router.post("/", response_model=TeamOut, status_code=201)
def create_team(
    data: TeamCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    team = Team(name=data.name, description=data.description, owner_id=current_user.id)
    db.add(team)
    db.flush()
    db.add(TeamMember(team_id=team.id, user_id=current_user.id, role="owner"))
    db.commit()
    db.refresh(team)
    return team


@router.get("/", response_model=List[TeamOut])
def list_teams(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    memberships = db.query(TeamMember).filter(TeamMember.user_id == current_user.id).all()
    team_ids    = [m.team_id for m in memberships]
    return db.query(Team).filter(Team.id.in_(team_ids)).all()


@router.get("/{team_id}", response_model=TeamOut)
def get_team(
    team_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    team = _get_team_or_404(db, team_id)
    _assert_member(db, team_id, current_user.id)
    return team


@router.delete("/{team_id}", status_code=204)
def delete_team(
    team_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    team = _get_team_or_404(db, team_id)
    _assert_owner(team, current_user)
    db.query(TeamMember).filter(TeamMember.team_id == team_id).delete()
    db.query(TeamInvite).filter(TeamInvite.team_id == team_id).delete()
    db.query(TeamProject).filter(TeamProject.team_id == team_id).delete()
    db.delete(team)
    db.commit()


# ════════════════════════════════════════════════
#  MEMBERS
# ════════════════════════════════════════════════

@router.get("/{team_id}/members", response_model=List[TeamMemberOut])
def list_members(
    team_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _assert_member(db, team_id, current_user.id)
    rows = (
        db.query(TeamMember, User)
        .join(User, User.id == TeamMember.user_id)
        .filter(TeamMember.team_id == team_id)
        .all()
    )
    return [
        TeamMemberOut(id=u.id, username=u.username, email=u.email, role=m.role)
        for m, u in rows
    ]


@router.delete("/{team_id}/members/{user_id}", status_code=204)
def remove_member(
    team_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    team = _get_team_or_404(db, team_id)
    if team.owner_id != current_user.id and current_user.id != user_id:
        raise HTTPException(403, "Not authorized")
    if user_id == team.owner_id:
        raise HTTPException(400, "Cannot remove the team owner")
    m = db.query(TeamMember).filter(
        TeamMember.team_id == team_id,
        TeamMember.user_id == user_id,
    ).first()
    if m:
        db.delete(m)
        db.commit()


# ════════════════════════════════════════════════
#  INVITATIONS — con Resend, funciona en producción
# ════════════════════════════════════════════════

@router.post("/{team_id}/invite", status_code=200)
def invite_member(
    team_id: int,
    data: TeamInviteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    team = _get_team_or_404(db, team_id)
    _assert_owner(team, current_user)

    # Si el email ya es miembro del equipo, rechazar
    existing_user = db.query(User).filter(User.email == data.email).first()
    if existing_user:
        already = db.query(TeamMember).filter(
            TeamMember.team_id == team_id,
            TeamMember.user_id == existing_user.id,
        ).first()
        if already:
            raise HTTPException(400, "This user is already a member of the team")

    # Cancelar invitaciones pendientes anteriores para este email
    db.query(TeamInvite).filter(
        TeamInvite.team_id  == team_id,
        TeamInvite.email    == data.email,
        TeamInvite.accepted == 0,
    ).update({"accepted": 2})
    db.commit()

    # Crear nueva invitación
    token  = secrets.token_urlsafe(32)
    invite = TeamInvite(team_id=team_id, email=data.email, token=token)
    db.add(invite)
    db.commit()

    # Enviar email con Resend (no bloquea aunque falle)
    
    try: email_sent = send_team_invite_email(
        to_email=data.email,
        team_name=team.name,
        invite_token=token,
        inviter_name=current_user.username,
    )
    except Exception as e:
     print(f"EMAIL ERROR: {e}")
    email_sent = False

    return {
        "message":        f"Invitation sent to {data.email}",
        "email_sent":     email_sent,
        "invite_token":   token,           
        "needs_register": existing_user is None,
        "team_name":      team.name,
    }


@router.get("/{team_id}/invites", response_model=List[TeamInviteOut])
def list_invites(
    team_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    team = _get_team_or_404(db, team_id)
    _assert_owner(team, current_user)
    return db.query(TeamInvite).filter(
        TeamInvite.team_id  == team_id,
        TeamInvite.accepted == 0,
    ).order_by(TeamInvite.created_at.desc()).all()


@router.delete("/{team_id}/invites/{invite_id}", status_code=204)
def cancel_invite(
    team_id:   int,
    invite_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    team = _get_team_or_404(db, team_id)
    _assert_owner(team, current_user)
    invite = db.query(TeamInvite).filter(
        TeamInvite.id      == invite_id,
        TeamInvite.team_id == team_id,
    ).first()
    if not invite:
        raise HTTPException(404, "Invite not found")
    db.delete(invite)
    db.commit()


@router.post("/invites/accept", status_code=200)
def accept_invite(
    token: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    invite = db.query(TeamInvite).filter(
        TeamInvite.token    == token,
        TeamInvite.accepted == 0,
    ).first()
    if not invite:
        raise HTTPException(400, "Invalid or already used invite token")

    # Validar que el email coincide si el usuario ya existía al crear el invite
    original_user = db.query(User).filter(User.email == invite.email).first()
    if original_user and original_user.id != current_user.id:
        raise HTTPException(403, "This invite was sent to a different email address")

    existing = db.query(TeamMember).filter(
        TeamMember.team_id == invite.team_id,
        TeamMember.user_id == current_user.id,
    ).first()
    if existing:
        raise HTTPException(400, "You are already a member of this team")

    db.add(TeamMember(team_id=invite.team_id, user_id=current_user.id, role="member"))
    invite.accepted = 1
    db.commit()
    return {"message": "You have joined the team!", "team_id": invite.team_id}


# ════════════════════════════════════════════════
#  TEAM PROJECTS
# ════════════════════════════════════════════════

@router.post("/{team_id}/projects", response_model=TeamProjectOut, status_code=201)
def create_project(
    team_id: int,
    data: TeamProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _assert_member(db, team_id, current_user.id)
    project = TeamProject(name=data.name, description=data.description, team_id=team_id)
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


@router.get("/{team_id}/projects", response_model=List[TeamProjectOut])
def list_projects(
    team_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _assert_member(db, team_id, current_user.id)
    return db.query(TeamProject).filter(TeamProject.team_id == team_id).all()
