import smtplib
from email.message import EmailMessage

from config.settings import get_settings

settings = get_settings()


def send_email(subject: str, recipient: str, html_body: str) -> None:
    if not settings.smtp_enabled:
        return
    smtp_user = settings.smtp_user or settings.email_user
    smtp_password = settings.smtp_password or settings.email_password
    if not smtp_user or not smtp_password:
        return

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = settings.smtp_from_email or smtp_user
    msg["To"] = recipient
    msg.set_content("Your email client does not support HTML.")
    msg.add_alternative(html_body, subtype="html")

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=20) as server:
        server.starttls()
        server.login(smtp_user, smtp_password)
        server.send_message(msg)


def send_signup_confirmation(recipient: str, name: str) -> None:
    subject = "Welcome to Self-Trust Score"
    html = f"""
    <h2>Welcome, {name}</h2>
    <p>Your account was created successfully.</p>
    <p>Stay consistent and keep building your self-trust.</p>
    """
    send_email(subject=subject, recipient=recipient, html_body=html)


def send_login_notification(recipient: str, name: str) -> None:
    subject = "New Login Detected"
    html = f"""
    <h2>Hello, {name}</h2>
    <p>A new login to your Self-Trust Score account was detected.</p>
    <p>If this was not you, reset your password immediately.</p>
    """
    send_email(subject=subject, recipient=recipient, html_body=html)
