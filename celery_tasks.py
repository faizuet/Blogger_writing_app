import os
import asyncio
import logging
from celery_app import celery_app
from fastapi_mail import FastMail, MessageSchema, MessageType
from email_config import MAIL_CONFIG

# ---------------- Logging Setup ----------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------------- Base URL ----------------
BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")

# ---------------- Email Sender ----------------
async def _send_email_async(subject: str, recipient: str, body: str):
    """Send an email asynchronously using FastMail."""
    try:
        mailer = FastMail(MAIL_CONFIG)
        message = MessageSchema(
            subject=subject,
            recipients=[recipient],
            body=body,
            subtype=MessageType.html,
        )
        await mailer.send_message(message)
        logger.info(f"[Email Sent] {subject} → {recipient}")
    except Exception as e:
        logger.exception(f"[Email Error] {subject} → {recipient}: {e}")
        raise


def send_email(subject: str, recipient: str, body: str):
    """Wrapper to safely run the async email sender inside Celery."""
    asyncio.run(_send_email_async(subject, recipient, body))

# ---------------- Celery Tasks ----------------
@celery_app.task(name="send_verification_email")
def send_verification_email(email: str, token: str):
    """Send verification email to a user."""
    verification_link = f"{BASE_URL}/auth/verify-email?token={token}"
    subject = "Verify Your Email"
    body = f"""
    <h2>Welcome to My Blog App!</h2>
    <p>Click the link below to verify your email:</p>
    <a href="{verification_link}" target="_blank">{verification_link}</a>
    """
    send_email(subject, email, body)
    return f"Verification email sent to {email}"


@celery_app.task(name="send_password_reset_email")
def send_password_reset_email(email: str, token: str):
    """Send password reset email to a user."""
    reset_link = f"{BASE_URL}/auth/reset-password?token={token}"
    subject = "Reset Your Password"
    body = f"""
    <h2>Password Reset Request</h2>
    <p>Click the link below to reset your password:</p>
    <a href="{reset_link}" target="_blank">{reset_link}</a>
    """
    send_email(subject, email, body)
    return f"Password reset email sent to {email}"

