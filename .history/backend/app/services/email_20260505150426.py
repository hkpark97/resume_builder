import requests
from app.config import settings


def send_password_reset_email(to_email: str, reset_url: str):
    subject = "Reset your Resumagic password"

    html = f"""
    <div>
      <h2>Reset your password</h2>
      <p>Click the link below to reset your password. This link expires in 30 minutes.</p>
      <p><a href="{reset_url}">Reset password</a></p>
      <p>If you did not request this, you can ignore this email.</p>
    </div>
    """

    if settings.email_provider == "console":
        print("PASSWORD RESET EMAIL")
        print("To:", to_email)
        print("Reset URL:", reset_url)
        return

    if settings.email_provider == "resend":
        response = requests.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {settings.resend_api_key}",
                "Content-Type": "application/json",
            },
            json={
                "from": settings.email_from,
                "to": [to_email],
                "subject": subject,
                "html": html,
            },
            timeout=20,
        )
        response.raise_for_status()
        return