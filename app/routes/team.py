from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import secrets, os

import resend

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

router = APIRouter(prefix="/teams", tags=["teams"])

# ─────────────────────────────────────────────
# RESEND CONFIG
# ─────────────────────────────────────────────
resend.api_key = os.getenv("RESEND_API_KEY")


# ── helpers ───────────────────────────────────
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
        TeamMember.user_id == user_id
    ).first()
    if not m:
        raise HTTPException(403, "You are not a member of this team")


# ─────────────────────────────────────────────
# EMAIL (RESEND)
# ─────────────────────────────────────────────
def _send_invite_email(to_email: str, team_name: str, invite_token: str, inviter_name: str):
    app_url = os.getenv("APP_URL", "https://taskflow-frontend-taupe.vercel.app")
    accept_url = f"{app_url}/invite/accept?token={invite_token}"

    html = f"""
    <div style="font-family:Arial,sans-serif;max-width:520px;margin:auto;background:#0b0d12;color:#eaeef7;padding:24px;border-radius:12px">
        <h2 style="color:#7c6dfa">You were invited to join {team_name}</h2>

        <p>
            <strong>{inviter_name}</strong> invited you to collaborate on TaskFlow.
        </p>

        <a href="{accept_url}"
           style="display:inline-block;margin-top:16px;padding:12px 20px;
           background:#7c6dfa;color:white;text-decoration:none;border-radius:8px">
           Accept Invitation
        </a>

        <p style="margin-top:20px;font-size:12px;color:#888">
            If you don't have an account, you can register first.
        </p>
    </div>
    """

    try:
        resend.Emails.send({
            # Usa tu Gmail verificado en Resend como remitente
            "from": f"{inviter_name} <{os.getenv('SMTP_USER')}>",
            "to": to_email,
            "subject": f"Invitation to join {team_name}",
            "html": html
        })
        return True
    except Exception as e:
        print("[Resend error]", e)
        return False



# ════════════════════════════════════════════════
# TEAM CRUD
# ════════════════════════════════════════════════

@router.post("/", response_model=TeamOut, status_code=201)
def create_team(
    data: TeamCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    team = Team(
        name=data.name,
        description=data.description,
        owner_id=current_user.id
    )
    db.add(team)
    db.flush()

    member = TeamMember(
        team_id=team.id,
        user_id=current_user.id,
        role="owner"
    )

    db.add(member)
    db.commit()
    db.refresh(team)
    return team


@router.get("/", response_model=List[TeamOut])
def list_teams(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    memberships = db.query(TeamMember).filter(
        TeamMember.user_id == current_user.id
    ).all()

    team_ids = [m.team_id for m in memberships]

    return db.query(Team).filter(Team.id.in_(team_ids)).all()


@router.get("/{team_id}", response_model=TeamOut)
def get_team(team_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    team = _get_team_or_404(db, team_id)
    _assert_member(db, team_id, current_user.id)
    return team


# ════════════════════════════════════════════════
# DELETE TEAM
# ════════════════════════════════════════════════

@router.delete("/{team_id}", status_code=204)
def delete_team(team_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    team = _get_team_or_404(db, team_id)
    _assert_owner(team, current_user)

    db.query(TeamMember).filter(TeamMember.team_id == team_id).delete()
    db.query(TeamInvite).filter(TeamInvite.team_id == team_id).delete()
    db.query(TeamProject).filter(TeamProject.team_id == team_id).delete()

    db.delete(team)
    db.commit()


# ════════════════════════════════════════════════
# MEMBERS
# ════════════════════════════════════════════════

@router.get("/{team_id}/members", response_model=List[TeamMemberOut])
def list_members(team_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
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
def remove_member(team_id: int, user_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    team = _get_team_or_404(db, team_id)

    if team.owner_id != current_user.id and current_user.id != user_id:
        raise HTTPException(403, "Not authorized")

    if user_id == team.owner_id:
        raise HTTPException(400, "Cannot remove owner")

    m = db.query(TeamMember).filter(
        TeamMember.team_id == team_id,
        TeamMember.user_id == user_id
    ).first()

    if m:
        db.delete(m)
        db.commit()


@router.post("/{team_id}/invite", status_code=200)
def invite_member(
    team_id: int,
    data: TeamInviteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    team = _get_team_or_404(db, team_id)
    _assert_owner(team, current_user)

    existing_user = db.query(User).filter(User.email == data.email).first()

    if existing_user:
        already = db.query(TeamMember).filter(
            TeamMember.team_id == team_id,
            TeamMember.user_id == existing_user.id
        ).first()
        if already:
            raise HTTPException(400, "Already a member")

    # Cancelar invitaciones previas pendientes
    db.query(TeamInvite).filter(
        TeamInvite.team_id == team_id,
        TeamInvite.email == data.email,
        TeamInvite.accepted == "pending"
    ).update({"accepted": "cancelled"})
    db.commit()

    # Crear nueva invitación
    token = secrets.token_urlsafe(32)
    invite = TeamInvite(
        team_id=team_id,
        email=data.email,
        token=token,
        accepted="pending"
    )
    db.add(invite)
    db.commit()

    # Enviar correo con Resend
    email_sent = _send_invite_email(
        to_email=data.email,
        team_name=team.name,
        invite_token=token,
        inviter_name=current_user.username,
    )

    return {
        "message": f"Invitation sent to {data.email}",
        "email_sent": email_sent,
        "invite_token": token,
        "team_name": team.name,
        "needs_register": existing_user is None,
    }



@router.get("/{team_id}/invites", response_model=List[TeamInviteOut])
def list_invites(team_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    team = _get_team_or_404(db, team_id)
    _assert_owner(team, current_user)

    return db.query(TeamInvite).filter(
        TeamInvite.team_id == team_id,
        TeamInvite.accepted == 0
    ).all()


@router.delete("/{team_id}/invites/{invite_id}", status_code=204)
def cancel_invite(team_id: int, invite_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    team = _get_team_or_404(db, team_id)
    _assert_owner(team, current_user)

    invite = db.query(TeamInvite).filter(
        TeamInvite.id == invite_id,
        TeamInvite.team_id == team_id
    ).first()

    if not invite:
        raise HTTPException(404, "Invite not found")

    db.delete(invite)
    db.commit()


# ════════════════════════════════════════════════
# ACCEPT INVITE
# ════════════════════════════════════════════════

@router.post("/invites/accept", status_code=200)
def accept_invite(token: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):

    invite = db.query(TeamInvite).filter(
        TeamInvite.token == token,
        TeamInvite.accepted == 0
    ).first()

    if not invite:
        raise HTTPException(400, "Invalid token")

    existing = db.query(TeamMember).filter(
        TeamMember.team_id == invite.team_id,
        TeamMember.user_id == current_user.id
    ).first()

    if existing:
        raise HTTPException(400, "Already member")

    db.add(TeamMember(
        team_id=invite.team_id,
        user_id=current_user.id,
        role="member"
    ))

    invite.accepted = 1
    db.commit()

    return {"message": "Joined team", "team_id": invite.team_id}


# ════════════════════════════════════════════════
# PROJECTS
# ════════════════════════════════════════════════

@router.post("/{team_id}/projects", response_model=TeamProjectOut)
def create_project(team_id: int, data: TeamProjectCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _assert_member(db, team_id, current_user.id)

    project = TeamProject(
        name=data.name,
        description=data.description,
        team_id=team_id
    )

    db.add(project)
    db.commit()
    db.refresh(project)

    return project


@router.get("/{team_id}/projects", response_model=List[TeamProjectOut])
def list_projects(team_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _assert_member(db, team_id, current_user.id)

    return db.query(TeamProject).filter(
        TeamProject.team_id == team_id
    ).all()