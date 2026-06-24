from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import secrets, os, smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

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
        TeamMember.user_id == user_id
    ).first()
    if not m:
        raise HTTPException(403, "You are not a member of this team")

def _send_invite_email(to_email: str, team_name: str, invite_token: str, inviter_name: str):
    
    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = int(os.getenv("SMTP_PORT", 587))
    smtp_user = os.getenv("SMTP_USER")
    smtp_pass = os.getenv("SMTP_PASS")
    app_url   = os.getenv("APP_URL", "https://taskflow-frontend-taupe.vercel.app")

    if not all([smtp_host, smtp_user, smtp_pass]):
        # SMTP not configured — skip silently (token still returned in response)
        return False

    accept_url = f"{app_url}/invite/accept?token={invite_token}"

    html = f"""
    <div style="font-family:Arial,sans-serif;max-width:520px;margin:0 auto;background:#07080d;color:#eef0f8;border-radius:16px;overflow:hidden">
      <div style="background:linear-gradient(135deg,#7c6dfa,#00e5b3);padding:32px 36px;text-align:center">
        <div style="font-size:32px;margin-bottom:8px">⚡</div>
        <div style="font-size:24px;font-weight:800;color:#fff">TaskFlow</div>
      </div>
      <div style="padding:36px">
        <h2 style="font-size:22px;font-weight:700;margin-bottom:12px;color:#eef0f8">
          You've been invited to join <span style="color:#7c6dfa">{team_name}</span>
        </h2>
        <p style="color:#8891b0;font-size:15px;line-height:1.6;margin-bottom:28px">
          <strong style="color:#eef0f8">{inviter_name}</strong> invited you to collaborate on
          <strong style="color:#eef0f8">{team_name}</strong> in TaskFlow — a professional
          project management platform.
        </p>
        <a href="{accept_url}"
           style="display:inline-block;background:linear-gradient(135deg,#7c6dfa,#5e52e0);
                  color:#fff;padding:14px 32px;border-radius:10px;text-decoration:none;
                  font-weight:700;font-size:15px">
          Accept Invitation →
        </a>
        <p style="color:#3d4460;font-size:12px;margin-top:24px;line-height:1.5">
          If you don't have a TaskFlow account yet, you'll be prompted to create one
          before accepting. This invitation expires in 7 days.<br/><br/>
          Or copy this link: <span style="color:#7c6dfa">{accept_url}</span>
        </p>
      </div>
    </div>
    """

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"You're invited to join {team_name} on TaskFlow"
        msg["From"]    = smtp_user
        msg["To"]      = to_email
        msg.attach(MIMEText(html, "html"))

        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.sendmail(smtp_user, to_email, msg.as_string())
        return True
    except Exception as e:
        print(f"[Email error] {e}")
        return False


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
    member = TeamMember(team_id=team.id, user_id=current_user.id, role="owner")
    db.add(member)
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


# ── NEW: Delete team ──────────────────────────────────────────────────────
@router.delete("/{team_id}", status_code=204)
def delete_team(
    team_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete the team. Only the owner can do this. Cascades to members + invites."""
    team = _get_team_or_404(db, team_id)
    _assert_owner(team, current_user)

    # Remove members, invites, projects (if cascade not set on DB)
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
    return [TeamMemberOut(id=u.id, username=u.username, email=u.email, role=m.role) for m, u in rows]


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
    m = db.query(TeamMember).filter(TeamMember.team_id == team_id, TeamMember.user_id == user_id).first()
    if m:
        db.delete(m)
        db.commit()


# ════════════════════════════════════════════════
#  INVITATIONS  (works even if email is unregistered)
# ════════════════════════════════════════════════

@router.post("/{team_id}/invite", status_code=200)
def invite_member(
    team_id: int,
    data: TeamInviteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Send an invite to ANY email address — the recipient does NOT need to
    have a TaskFlow account. If they don't, they'll register first and
    then use the token to join the team.
    """
    team = _get_team_or_404(db, team_id)
    _assert_owner(team, current_user)

    # Check if already a member (only if they have an account)
    existing_user = db.query(User).filter(User.email == data.email).first()
    if existing_user:
        already = db.query(TeamMember).filter(
            TeamMember.team_id == team_id,
            TeamMember.user_id == existing_user.id
        ).first()
        if already:
            raise HTTPException(400, "This user is already a member of the team")

    # Cancel any pending invite for this email on this team
    db.query(TeamInvite).filter(
        TeamInvite.team_id == team_id,
        TeamInvite.email   == data.email,
        TeamInvite.accepted == 0,
    ).update({"accepted": 2})   # 2 = cancelled/superseded
    db.commit()

    token  = secrets.token_urlsafe(32)
    invite = TeamInvite(team_id=team_id, email=data.email, token=token)
    db.add(invite)
    db.commit()

    email_sent = _send_invite_email(
        to_email    = data.email,
        team_name   = team.name,
        invite_token= token,
        inviter_name= current_user.username,
    )

    return {
        "message":       f"Invitation sent to {data.email}",
        "email_sent":    email_sent,
        "invite_token":  token,          # always returned so dev can test without SMTP
        "team_name":     team.name,
        "needs_register": existing_user is None,
        "dev_note":      "Configure SMTP_HOST/SMTP_USER/SMTP_PASS in .env to send real emails",
    }


# ── NEW: List pending invites for a team ─────────────────────────────────
@router.get("/{team_id}/invites", response_model=List[TeamInviteOut])
def list_invites(
    team_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    team = _get_team_or_404(db, team_id)
    _assert_owner(team, current_user)
    invites = db.query(TeamInvite).filter(
        TeamInvite.team_id  == team_id,
        TeamInvite.accepted == 0,
    ).order_by(TeamInvite.created_at.desc()).all()
    return invites


# ── NEW: Cancel a pending invite ──────────────────────────────────────────
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


# ── Accept invite (works for both registered and new users) ───────────────
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

    # Allow the invite if:
    # a) The invite was sent to the user's email, OR
    # b) The invite has no matching registered user (was sent to an unregistered email)
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
