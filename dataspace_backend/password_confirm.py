from __future__ import annotations

from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response


def verify_confirm_password(request: Request) -> Response | None:
    """Return an error Response if the password confirmation is missing or
    invalid, or ``None`` when the caller may proceed normally.

    The password is read from ``request.data["password"]`` first, then from
    the ``X-Confirm-Password`` header (useful for DELETE requests that
    typically carry no body).
    """
    password = request.data.get("password") or request.headers.get(
        "X-Confirm-Password"
    )

    if not password:
        return Response(
            {"detail": "Password confirmation is required."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if not request.user.check_password(password):
        return Response(
            {"detail": "Invalid password."},
            status=status.HTTP_403_FORBIDDEN,
        )

    return None
