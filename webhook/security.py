"""
Webhook signature verification for iGrant.io webhook security.

Implements HMAC-SHA256 signature verification as described in:
https://docs.igrant.io/docs/openid4vc-webhooks/#webhook-security

The webhook sender includes an X-iGrant-Signature header with the format:
    t=<timestamp>,sig=<signature>

The signature is computed as:
    HMAC-SHA256(secret_key, timestamp + "." + request_body)
"""

import hashlib
import hmac
import logging
from datetime import datetime, timedelta, timezone
from functools import wraps

from django.conf import settings
from django.http import HttpRequest, HttpResponse
from rest_framework import status

logger = logging.getLogger(__name__)

SIGNATURE_HEADER = "X-iGrant-Signature"
TIMESTAMP_TOLERANCE = timedelta(minutes=5)


def _parse_signature_header(header_value: str) -> tuple[str, str]:
    """
    Parse the X-iGrant-Signature header.

    Expected format: "t=<timestamp>,sig=<signature>"

    Returns:
        Tuple of (timestamp, signature).

    Raises:
        ValueError: If the header format is invalid.
    """
    parts = {}
    for part in header_value.split(","):
        key, _, value = part.strip().partition("=")
        if key and value:
            parts[key] = value

    if "t" not in parts or "sig" not in parts:
        raise ValueError("Missing 't' or 'sig' in signature header")

    return parts["t"], parts["sig"]


def _verify_signature(
    timestamp: str, signature: str, secret_key: str, payload: bytes
) -> bool:
    """
    Verify the HMAC-SHA256 webhook signature.

    The signed payload is: timestamp + "." + request_body
    """
    signed_payload = timestamp + "." + payload.decode("utf-8")
    computed_sig = hmac.new(
        secret_key.encode("utf-8"),
        signed_payload.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(computed_sig, signature)


def _is_timestamp_recent(timestamp: str) -> bool:
    """
    Check that the timestamp is within the allowed tolerance window.

    The timestamp is expected to be in ISO 8601 UTC format.
    """
    try:
        ts = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        return abs(now - ts) <= TIMESTAMP_TOLERANCE
    except (ValueError, TypeError):
        return False


def verify_webhook(view_func):
    """
    Decorator that verifies the iGrant.io webhook signature.

    Checks:
    1. WEBHOOK_SECRET_KEY is configured
    2. X-iGrant-Signature header is present and well-formed
    3. Timestamp is within 5 minutes of current time
    4. HMAC-SHA256 signature matches

    If WEBHOOK_SECRET_KEY is not configured, the webhook is allowed through
    without verification (to support development/migration).
    """

    @wraps(view_func)
    def wrapper(request: HttpRequest, *args, **kwargs) -> HttpResponse:
        secret_key = getattr(settings, "WEBHOOK_SECRET_KEY", None)

        if not secret_key:
            logger.warning(
                "WEBHOOK_SECRET_KEY not configured, skipping signature verification"
            )
            return view_func(request, *args, **kwargs)

        signature_header = request.META.get("HTTP_X_IGRANT_SIGNATURE")
        if not signature_header:
            logger.warning("Missing %s header", SIGNATURE_HEADER)
            return HttpResponse(
                "Missing signature header",
                status=status.HTTP_401_UNAUTHORIZED,
            )

        try:
            timestamp, signature = _parse_signature_header(signature_header)
        except ValueError:
            logger.warning("Malformed %s header", SIGNATURE_HEADER)
            return HttpResponse(
                "Malformed signature header",
                status=status.HTTP_401_UNAUTHORIZED,
            )

        if not _is_timestamp_recent(timestamp):
            logger.warning("Webhook timestamp outside tolerance window: %s", timestamp)
            return HttpResponse(
                "Timestamp out of tolerance",
                status=status.HTTP_401_UNAUTHORIZED,
            )

        if not _verify_signature(timestamp, signature, secret_key, request.body):
            logger.warning("Webhook signature verification failed")
            return HttpResponse(
                "Invalid signature",
                status=status.HTTP_401_UNAUTHORIZED,
            )

        return view_func(request, *args, **kwargs)

    return wrapper
