from __future__ import annotations

import logging
import smtplib
from datetime import timedelta
from email.mime.text import MIMEText

from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)


def send_mfa_code_email(email: str, code: str) -> None:
    """Send a 6-digit MFA verification code to the user's email."""
    expiry_minutes = settings.MFA_CODE_EXPIRY_SECONDS // 60
    body = f"Your verification code is: {code}\n\nThis code expires in {expiry_minutes} minutes."

    msg = MIMEText(body)
    msg["Subject"] = "Your verification code"
    msg["From"] = f"CRANE d-HDSI Data Marketplace <{settings.SMTP_ADMIN_EMAIL}>"
    msg["Reply-To"] = "no-reply@igrant.io"
    msg["To"] = email

    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
        server.starttls()
        if settings.SMTP_USERNAME and settings.SMTP_PASSWORD:
            server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
        server.sendmail(settings.SMTP_ADMIN_EMAIL, [email], msg.as_string())

    logger.info("MFA code sent to %s", email)


def cleanup_expired_mfa_codes() -> None:
    """Delete MFA codes that have expired. Called opportunistically during login."""
    from onboard.models import MFACode

    cutoff = timezone.now() - timedelta(seconds=settings.MFA_CODE_EXPIRY_SECONDS)
    deleted_count, _ = MFACode.objects.filter(created_at__lt=cutoff).delete()
    if deleted_count:
        logger.info("Cleaned up %d expired MFA codes", deleted_count)
