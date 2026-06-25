import os
import resend

resend.api_key = os.getenv("RESEND_API_KEY")

APP_URL = os.getenv(
    "APP_URL",
    "https://taskflow-frontend-taupe.vercel.app"
)

FROM_EMAIL = "TaskFlow <onboarding@resend.dev>"


def send_team_invite_email(
    to_email: str,
    team_name: str,
    invite_token: str,
    inviter_name: str,
) -> bool:
    try:
        invite_url = f"{APP_URL}/invite/accept?token={invite_token}"

        resend.Emails.send({
            "from": FROM_EMAIL,
            "to": [to_email],
            "subject": f"{inviter_name} invited you to join {team_name}",
            "html": f"""
            <div style="font-family:Arial;padding:30px">
                <h2>You've been invited to join {team_name} 🎉</h2>

                <p>
                    <strong>{inviter_name}</strong> invited you to collaborate
                    in TaskFlow.
                </p>

                <p>
                    Click the button below to accept the invitation:
                </p>

                <a
                    href="{invite_url}"
                    style="
                        display:inline-block;
                        padding:14px 28px;
                        background:#7c6dfa;
                        color:white;
                        text-decoration:none;
                        border-radius:8px;
                        font-weight:bold;
                    "
                >
                    Accept Invitation
                </a>

                <br><br>

                <p>If the button doesn't work:</p>

                <p>{invite_url}</p>
            </div>
            """
        })

        print(f"[Email] Invitation sent to {to_email}")
        return True

    except Exception as e:
        print(f"[Resend] ERROR: {e}")
        return False


def send_password_reset_email(
    to_email: str,
    reset_token: str,
    username: str,
) -> bool:
    try:
        reset_url = f"{APP_URL}/reset-password?token={reset_token}"

        resend.Emails.send({
            "from": FROM_EMAIL,
            "to": [to_email],
            "subject": "Reset your TaskFlow password",
            "html": f"""
            <div style="font-family:Arial;padding:30px">
                <h2>Password Reset</h2>

                <p>Hello {username},</p>

                <p>
                    Click the button below to reset your password:
                </p>

                <a
                    href="{reset_url}"
                    style="
                        display:inline-block;
                        padding:14px 28px;
                        background:#7c6dfa;
                        color:white;
                        text-decoration:none;
                        border-radius:8px;
                        font-weight:bold;
                    "
                >
                    Reset Password
                </a>

                <br><br>

                <p>If the button doesn't work:</p>

                <p>{reset_url}</p>
            </div>
            """
        })

        print(f"[Email] Password reset email sent to {to_email}")
        return True

    except Exception as e:
        print(f"[Resend] ERROR: {e}")
        return False