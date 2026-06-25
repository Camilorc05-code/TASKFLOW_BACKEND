import os
import httpx
 
# ── Config desde .env ─────────────────────────────────────────────────────
GMAIL_USER = os.getenv("GMAIL_USER", "jhojancamilorodriguez2017@gmail.com")   # tu@gmail.com
GMAIL_PASS = os.getenv("GMAIL_PASS", "jcbx qwqi npsv fsrr")   
APP_URL    = os.getenv("APP_URL", "https://taskflow-frontend-taupe.vercel.app/")
FROM_NAME  = os.getenv("FROM_NAME", "TaskFlow")
 
 
def _send_via_gmail_api(to_email: str, subject: str, html: str) -> bool:
    """
    Envía email usando la API HTTP de Gmail (OAuth2 no requerido).
    Usa httpx en modo síncrono — rápido y compatible con Render.
    """
    if not GMAIL_USER or not GMAIL_PASS:
        print("[Email] GMAIL_USER o GMAIL_PASS no configurados")
        return False
 
    # Construir el mensaje MIME en base64 para la API de Gmail
    import smtplib
    import ssl
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText
 
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"]    = f"{FROM_NAME} <{GMAIL_USER}>"
        msg["To"]      = to_email
        msg.attach(MIMEText(html, "html"))
 
        # Usar httpx para conectar al SMTP de Gmail via SSL
        # Gmail puerto 465 (SSL directo, más rápido que 587+STARTTLS)
        context = ssl.create_default_context()
 
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context, timeout=15) as server:
            server.login(GMAIL_USER, GMAIL_PASS)
            server.sendmail(GMAIL_USER, to_email, msg.as_string())
 
        print(f"[Email] ✅ Enviado a {to_email}")
        return True
 
    except smtplib.SMTPAuthenticationError:
        print("[Email] ❌ Error de autenticación — verifica GMAIL_USER y GMAIL_PASS (App Password)")
        return False
    except smtplib.SMTPException as e:
        print(f"[Email] ❌ SMTP Error: {e}")
        return False
    except Exception as e:
        print(f"[Email] ❌ Error: {type(e).__name__}: {e}")
        return False
 
 
def send_team_invite_email(
    to_email:     str,
    team_name:    str,
    invite_token: str,
    inviter_name: str,
) -> bool:
    accept_url = f"{APP_URL}/invite/accept?token={invite_token}"
 
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width,initial-scale=1.0"/>
</head>
<body style="margin:0;padding:0;background:#07080d;font-family:'Segoe UI',Arial,sans-serif">
  <div style="max-width:560px;margin:40px auto;background:#111420;border-radius:20px;overflow:hidden;border:1px solid #1c2035">
 
    <div style="background:linear-gradient(135deg,#7c6dfa,#00e5b3);padding:36px;text-align:center">
      <div style="font-size:40px;margin-bottom:8px">⚡</div>
      <div style="font-size:28px;font-weight:800;color:#fff;letter-spacing:-0.5px">TaskFlow</div>
      <div style="font-size:13px;color:rgba(255,255,255,0.75);margin-top:4px">Project Management</div>
    </div>
 
    <div style="padding:40px 36px">
      <h2 style="font-size:22px;font-weight:700;color:#eef0f8;margin:0 0 14px">
        You've been invited to <span style="color:#7c6dfa">{team_name}</span> 🎉
      </h2>
      <p style="font-size:15px;color:#8891b0;line-height:1.7;margin:0 0 28px">
        <strong style="color:#eef0f8">{inviter_name}</strong> invited you to collaborate
        on <strong style="color:#eef0f8">{team_name}</strong> in TaskFlow —
        a professional project management platform with Kanban boards, sprints and more.
      </p>
 
      <div style="text-align:center;margin:32px 0">
        <a href="{accept_url}"
           style="display:inline-block;background:linear-gradient(135deg,#7c6dfa,#5e52e0);
                  color:#fff;padding:16px 44px;border-radius:12px;text-decoration:none;
                  font-weight:700;font-size:16px;
                  box-shadow:0 8px 24px rgba(124,109,250,0.45)">
          Accept Invitation →
        </a>
      </div>
 
      <div style="padding:14px 16px;background:rgba(124,109,250,0.07);border-radius:10px;
                  border:1px solid rgba(124,109,250,0.2);margin-bottom:24px">
        <p style="margin:0;font-size:13px;color:#8891b0;line-height:1.6">
          💡 <strong style="color:#eef0f8">New to TaskFlow?</strong>
          No problem — click the button and you'll be guided to create a free account first.
        </p>
      </div>
 
      <p style="font-size:12px;color:#3d4460;line-height:1.6;margin:0">
        Can't click the button? Paste this in your browser:<br/>
        <a href="{accept_url}" style="color:#7c6dfa;word-break:break-all">{accept_url}</a>
      </p>
      <p style="font-size:11px;color:#3d4460;margin-top:12px">
        This invitation expires in 7 days. Didn't expect this? You can safely ignore it.
      </p>
    </div>
 
    <div style="padding:18px 36px;border-top:1px solid #1c2035;text-align:center">
      <p style="margin:0;font-size:11px;color:#3d4460">TaskFlow · Built with FastAPI & React</p>
    </div>
  </div>
</body>
</html>"""
 
    return _send_via_gmail_api(
        to_email = to_email,
        subject  = f"You're invited to join {team_name} on TaskFlow",
        html     = html,
    )
 
 
def send_password_reset_email(
    to_email:    str,
    reset_token: str,
    username:    str,
) -> bool:
    reset_url = f"{APP_URL}/reset-password?token={reset_token}"
 
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width,initial-scale=1.0"/>
</head>
<body style="margin:0;padding:0;background:#07080d;font-family:'Segoe UI',Arial,sans-serif">
  <div style="max-width:520px;margin:40px auto;background:#111420;border-radius:20px;overflow:hidden;border:1px solid #1c2035">
 
    <div style="background:linear-gradient(135deg,#7c6dfa,#00e5b3);padding:32px;text-align:center">
      <div style="font-size:32px;margin-bottom:6px">🔐</div>
      <div style="font-size:22px;font-weight:800;color:#fff">TaskFlow</div>
    </div>
 
    <div style="padding:36px">
      <h2 style="font-size:20px;font-weight:700;color:#eef0f8;margin:0 0 10px">
        Reset your password
      </h2>
      <p style="font-size:14px;color:#8891b0;line-height:1.7;margin:0 0 24px">
        Hi <strong style="color:#eef0f8">{username}</strong>,
        we received a request to reset your TaskFlow password.
        Click below to choose a new one.
      </p>
 
      <div style="text-align:center;margin:28px 0">
        <a href="{reset_url}"
           style="display:inline-block;background:linear-gradient(135deg,#7c6dfa,#5e52e0);
                  color:#fff;padding:14px 36px;border-radius:12px;text-decoration:none;
                  font-weight:700;font-size:15px;
                  box-shadow:0 8px 24px rgba(124,109,250,0.4)">
          Reset Password →
        </a>
      </div>
 
      <div style="padding:12px 14px;background:rgba(255,84,112,0.06);border-radius:10px;
                  border:1px solid rgba(255,84,112,0.2);margin-bottom:20px">
        <p style="margin:0;font-size:13px;color:#8891b0">
          ⚠ Link expires in <strong style="color:#eef0f8">1 hour</strong>.
          If you didn't request this, ignore this email.
        </p>
      </div>
 
      <p style="font-size:12px;color:#3d4460;margin:0">
        Or paste in browser:
        <a href="{reset_url}" style="color:#7c6dfa;word-break:break-all">{reset_url}</a>
      </p>
    </div>
 
    <div style="padding:16px 36px;border-top:1px solid #1c2035;text-align:center">
      <p style="margin:0;font-size:11px;color:#3d4460">TaskFlow · Built with FastAPI & React</p>
    </div>
  </div>
</body>
</html>"""
 
    return _send_via_gmail_api(
        to_email = to_email,
        subject  = "Reset your TaskFlow password",
        html     = html,
    )
 