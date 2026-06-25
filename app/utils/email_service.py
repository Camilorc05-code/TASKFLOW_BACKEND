import os
import requests

BREVO_API_KEY = os.getenv("BREVO_API_KEY")
BREVO_SENDER_EMAIL = os.getenv("BREVO_SENDER_EMAIL")
BREVO_SENDER_NAME = os.getenv("BREVO_SENDER_NAME", "TaskFlow")
APP_URL = os.getenv(
    "APP_URL",
    "https://taskflow-frontend-taupe.vercel.app"
)


def send_email(
    to_email: str,
    subject: str,
    html: str
) -> bool:
    try:
        response = requests.post(
            "https://api.brevo.com/v3/smtp/email",
            headers={
                "accept": "application/json",
                "api-key": BREVO_API_KEY,
                "content-type": "application/json"
            },
            json={
                "sender": {
                    "name": BREVO_SENDER_NAME,
                    "email": BREVO_SENDER_EMAIL
                },
                "to": [
                    {
                        "email": to_email
                    }
                ],
                "subject": subject,
                "htmlContent": html
            },
            timeout=15
        )

        if response.status_code in [200, 201]:
            print(f"[Brevo] ✅ Email enviado a {to_email}")
            return True

        print(
            f"[Brevo] ❌ Error {response.status_code}: "
            f"{response.text}"
        )
        return False

    except Exception as e:
        print(f"[Brevo] ❌ Exception: {e}")
        return False


def send_team_invite_email(
    to_email: str,
    team_name: str,
    invite_token: str,
    inviter_name: str
) -> bool:

    accept_url = (
        f"{APP_URL}/invite/accept?token={invite_token}"
    )

    html = f"""
    <div style="font-family:Arial,sans-serif;padding:40px;background:#f5f5f5">
        <div style="max-width:600px;margin:auto;background:white;
                    padding:40px;border-radius:12px">

            <h1>⚡ TaskFlow</h1>

            <h2>You've been invited to join {team_name}</h2>

            <p>
                <strong>{inviter_name}</strong>
                invited you to collaborate in
                <strong>{team_name}</strong>.
            </p>

            <p>
                Click the button below to accept the invitation:
            </p>

            <a href="{accept_url}"
               style="
                    display:inline-block;
                    background:#7c6dfa;
                    color:white;
                    text-decoration:none;
                    padding:14px 24px;
                    border-radius:8px;
                    font-weight:bold;
               ">
               Accept Invitation
            </a>

            <p style="margin-top:30px;font-size:12px;color:#777">
                If the button does not work, copy this URL:
            </p>

            <p style="font-size:12px">
                {accept_url}
            </p>

        </div>
    </div>
    """

    return send_email(
        to_email=to_email,
        subject=f"Invitation to join {team_name} on TaskFlow",
        html=html
    )


def send_password_reset_email(
    to_email: str,
    reset_token: str,
    username: str
) -> bool:

    reset_url = (
        f"{APP_URL}/reset-password?token={reset_token}"
    )

    html = f"""
    <div style="font-family:Arial,sans-serif;padding:40px;background:#f5f5f5">
        <div style="max-width:600px;margin:auto;background:white;
                    padding:40px;border-radius:12px">

            <h1>🔐 TaskFlow</h1>

            <h2>Password Reset</h2>

            <p>
                Hello <strong>{username}</strong>,
            </p>

            <p>
                We received a request to reset your password.
            </p>

            <a href="{reset_url}"
               style="
                    display:inline-block;
                    background:#7c6dfa;
                    color:white;
                    text-decoration:none;
                    padding:14px 24px;
                    border-radius:8px;
                    font-weight:bold;
               ">
               Reset Password
            </a>

            <p style="margin-top:30px;font-size:12px;color:#777">
                If the button does not work, copy this URL:
            </p>

            <p style="font-size:12px">
                {reset_url}
            </p>

        </div>
    </div>
    """

    return send_email(
        to_email=to_email,
        subject="Reset your TaskFlow password",
        html=html
    )