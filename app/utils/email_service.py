import os
import resend
from typing import Optional

# Resend inicializa con la API key del entorno
resend.api_key = os.getenv("RESEND_API_KEY", "")

# Email desde el que se envían los correos.
# En Resend free tier DEBES usar: onboarding@resend.dev  (para pruebas)
# En producción: configura tu dominio en resend.com y usa tu@tudominio.com
FROM_EMAIL = os.getenv("FROM_EMAIL", "onboarding@resend.dev")
FROM_NAME  = os.getenv("FROM_NAME",  "TaskFlow")
APP_URL    = os.getenv("APP_URL",    "http://localhost:3000")


def send_team_invite_email(
    to_email:     str,
    team_name:    str,
    invite_token: str,
    inviter_name: str,
) -> bool:
    """
    Envía invitación de equipo usando Resend.
    Retorna True si se envió, False si falló.
    """
    if not resend.api_key:
        print("[Email] RESEND_API_KEY no configurada — omitiendo email")
        return False

    accept_url = f"{APP_URL}/invite/accept?token={invite_token}"

    html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>You're invited to {team_name}</title>
</head>
<body style="margin:0;padding:0;background:#07080d;font-family:'Segoe UI',Arial,sans-serif">
  <div style="max-width:560px;margin:40px auto;background:#111420;border-radius:20px;overflow:hidden;border:1px solid #1c2035">

    <!-- Header -->
    <div style="background:linear-gradient(135deg,#7c6dfa 0%,#00e5b3 100%);padding:36px;text-align:center">
      <div style="font-size:36px;margin-bottom:8px">⚡</div>
      <div style="font-size:26px;font-weight:800;color:#ffffff;letter-spacing:-0.5px">TaskFlow</div>
      <div style="font-size:13px;color:rgba(255,255,255,0.75);margin-top:4px">Project Management Platform</div>
    </div>

    <!-- Body -->
    <div style="padding:40px 36px">
      <h2 style="font-size:22px;font-weight:700;color:#eef0f8;margin:0 0 12px">
        You've been invited to join <span style="color:#7c6dfa">{team_name}</span>
      </h2>
      <p style="font-size:15px;color:#8891b0;line-height:1.7;margin:0 0 28px">
        <strong style="color:#eef0f8">{inviter_name}</strong> has invited you to collaborate
        on <strong style="color:#eef0f8">{team_name}</strong> in TaskFlow — a professional
        Jira-like task management platform built for developers.
      </p>

      <!-- CTA Button -->
      <div style="text-align:center;margin:32px 0">
        <a href="{accept_url}"
           style="display:inline-block;background:linear-gradient(135deg,#7c6dfa,#5e52e0);
                  color:#ffffff;padding:16px 40px;border-radius:12px;text-decoration:none;
                  font-weight:700;font-size:16px;letter-spacing:0.2px;
                  box-shadow:0 8px 24px rgba(124,109,250,0.4)">
          Accept Invitation →
        </a>
      </div>

      <!-- Info boxes -->
      <div style="display:flex;gap:12px;margin:28px 0">
        <div style="flex:1;padding:14px;background:#181c2a;border-radius:10px;border:1px solid #1c2035;text-align:center">
          <div style="font-size:20px;margin-bottom:6px">📋</div>
          <div style="font-size:12px;font-weight:600;color:#eef0f8">Kanban Boards</div>
          <div style="font-size:11px;color:#8891b0;margin-top:3px">Visual task management</div>
        </div>
        <div style="flex:1;padding:14px;background:#181c2a;border-radius:10px;border:1px solid #1c2035;text-align:center">
          <div style="font-size:20px;margin-bottom:6px">🚀</div>
          <div style="font-size:12px;font-weight:600;color:#eef0f8">Sprints</div>
          <div style="font-size:11px;color:#8891b0;margin-top:3px">Agile backlog & planning</div>
        </div>
        <div style="flex:1;padding:14px;background:#181c2a;border-radius:10px;border:1px solid #1c2035;text-align:center">
          <div style="font-size:20px;margin-bottom:6px">📅</div>
          <div style="font-size:12px;font-weight:600;color:#eef0f8">Calendar</div>
          <div style="font-size:11px;color:#8891b0;margin-top:3px">Timeline & deadlines</div>
        </div>
      </div>

      <!-- Note for new users -->
      <div style="padding:14px 16px;background:rgba(124,109,250,0.07);border-radius:10px;border:1px solid rgba(124,109,250,0.2);margin-bottom:24px">
        <p style="margin:0;font-size:13px;color:#8891b0;line-height:1.6">
          💡 <strong style="color:#eef0f8">New to TaskFlow?</strong>
          No problem — click the button above and you'll be guided to create a free account
          before joining the team.
        </p>
      </div>

      <!-- Link fallback -->
      <p style="font-size:12px;color:#3d4460;line-height:1.6;margin:0">
        Can't click the button? Copy and paste this link into your browser:<br/>
        <a href="{accept_url}" style="color:#7c6dfa;word-break:break-all">{accept_url}</a>
      </p>
      <p style="font-size:11px;color:#3d4460;margin-top:12px">
        This invitation expires in 7 days. If you didn't expect this email, you can safely ignore it.
      </p>
    </div>

    <!-- Footer -->
    <div style="padding:20px 36px;border-top:1px solid #1c2035;text-align:center">
      <p style="margin:0;font-size:12px;color:#3d4460">
        Sent by TaskFlow · Built with FastAPI & React
      </p>
    </div>
  </div>
</body>
</html>
"""

    try:
        params = resend.Emails.SendParams(
            from_=f"{FROM_NAME} <{FROM_EMAIL}>",
            to=[to_email],
            subject=f"You're invited to join {team_name} on TaskFlow",
            html=html,
        )
        response = resend.Emails.send(params)
        print(f"[Email] Sent to {to_email} — id: {response.get('id', 'unknown')}")
        return True
    except Exception as e:
        print(f"[Email] Error sending to {to_email}: {e}")
        return False


def send_password_reset_email(
    to_email:    str,
    reset_token: str,
    username:    str,
) -> bool:
    """
    Envía email de reset de contraseña usando Resend.
    """
    if not resend.api_key:
        print("[Email] RESEND_API_KEY no configurada — omitiendo email")
        return False

    reset_url = f"{APP_URL}/reset-password?token={reset_token}"

    html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>Reset your password</title>
</head>
<body style="margin:0;padding:0;background:#07080d;font-family:'Segoe UI',Arial,sans-serif">
  <div style="max-width:520px;margin:40px auto;background:#111420;border-radius:20px;overflow:hidden;border:1px solid #1c2035">

    <div style="background:linear-gradient(135deg,#7c6dfa 0%,#00e5b3 100%);padding:32px;text-align:center">
      <div style="font-size:32px;margin-bottom:6px">🔐</div>
      <div style="font-size:22px;font-weight:800;color:#fff">TaskFlow</div>
    </div>

    <div style="padding:36px">
      <h2 style="font-size:20px;font-weight:700;color:#eef0f8;margin:0 0 10px">
        Reset your password
      </h2>
      <p style="font-size:14px;color:#8891b0;line-height:1.7;margin:0 0 24px">
        Hi <strong style="color:#eef0f8">{username}</strong>, we received a request to reset your
        TaskFlow password. Click the button below to choose a new password.
      </p>

      <div style="text-align:center;margin:28px 0">
        <a href="{reset_url}"
           style="display:inline-block;background:linear-gradient(135deg,#7c6dfa,#5e52e0);
                  color:#fff;padding:14px 36px;border-radius:12px;text-decoration:none;
                  font-weight:700;font-size:15px;box-shadow:0 8px 24px rgba(124,109,250,0.4)">
          Reset Password →
        </a>
      </div>

      <div style="padding:12px 14px;background:rgba(255,84,112,0.06);border-radius:10px;border:1px solid rgba(255,84,112,0.2);margin-bottom:20px">
        <p style="margin:0;font-size:13px;color:#8891b0">
          ⚠ This link expires in <strong style="color:#eef0f8">1 hour</strong>.
          If you didn't request a password reset, you can safely ignore this email.
        </p>
      </div>

      <p style="font-size:12px;color:#3d4460;margin:0">
        Or copy: <a href="{reset_url}" style="color:#7c6dfa;word-break:break-all">{reset_url}</a>
      </p>
    </div>

    <div style="padding:16px 36px;border-top:1px solid #1c2035;text-align:center">
      <p style="margin:0;font-size:11px;color:#3d4460">TaskFlow · Built with FastAPI & React</p>
    </div>
  </div>
</body>
</html>
"""

    try:
        params = resend.Emails.SendParams(
            from_=f"{FROM_NAME} <{FROM_EMAIL}>",
            to=[to_email],
            subject="Reset your TaskFlow password",
            html=html,
        )
        response = resend.Emails.send(params)
        print(f"[Email] Password reset sent to {to_email} — id: {response.get('id', 'unknown')}")
        return True
    except Exception as e:
        print(f"[Email] Error sending reset to {to_email}: {e}")
        return False
