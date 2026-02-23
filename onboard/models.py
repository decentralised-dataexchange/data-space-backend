"""
Onboard Models Module

This module defines the user model for the data space platform. It provides
custom user authentication using email as the primary identifier instead of
username, which is the standard approach for modern web applications.
"""

from __future__ import annotations

import secrets
from uuid import uuid4

from django.conf import settings as django_settings
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from onboard.managers import DataspaceUserManager


class DataspaceUser(AbstractBaseUser, PermissionsMixin):
    """
    Custom user model for the data space platform.

    This model represents users who can register and authenticate within the
    data space ecosystem. Users are identified by their email address rather
    than a traditional username. Each user can be associated with an organisation
    as an administrator, enabling them to manage data agreements, connections,
    and other organisational resources.

    The model extends Django's AbstractBaseUser and PermissionsMixin to provide
    full authentication capabilities while allowing email-based login.

    Relationships:
        - One-to-One with Organisation: A user can be the admin of one organisation
        - One-to-One with DataSource: A user can manage one data source
    """

    # Public-facing unique identifier (replaces sequential integer ID in APIs/JWTs)
    uuid = models.UUIDField(default=uuid4, unique=True, editable=False)

    # Primary email address used for authentication and communication
    # This field serves as the unique identifier (USERNAME_FIELD) for login
    email: models.EmailField[str, str] = models.EmailField(
        _("email address"), unique=True
    )

    # Flag indicating whether the user can access the Django admin interface
    # Staff users have elevated privileges for system administration
    is_staff: models.BooleanField[bool, bool] = models.BooleanField(default=False)

    # Flag indicating whether the user account is active
    # Inactive users cannot log in; used for soft-deletion or account suspension
    is_active: models.BooleanField[bool, bool] = models.BooleanField(default=True)

    # Timestamp when the user account was created
    # Automatically set to the current time when the user registers
    date_joined: models.DateTimeField[str, str] = models.DateTimeField(
        default=timezone.now
    )

    # Optional display name for the user
    # Used for personalization in the UI and communications
    name: models.CharField[str | None, str | None] = models.CharField(
        max_length=250, null=True, blank=True
    )

    # Per-user MFA toggle; when True the user enters the MFA code flow at login
    is_mfa_enabled: models.BooleanField[bool, bool] = models.BooleanField(default=False)

    # Specifies that email is used as the unique identifier for authentication
    USERNAME_FIELD: str = "email"

    # No additional required fields beyond email (password is handled by AbstractBaseUser)
    REQUIRED_FIELDS: "list[str]" = []  # type: ignore[misc]

    # Custom manager that handles user creation with email as the identifier
    objects: "DataspaceUserManager" = DataspaceUserManager()  # type: ignore[misc]

    def __str__(self) -> str:
        return str(self.email)


class MFACode(models.Model):
    """
    Stores a pending MFA verification code tied to a login session.

    Created after successful password validation when MFA is enabled.
    The session_token is returned to the client so it can be used to
    submit the 6-digit code for verification.
    """

    session_token = models.UUIDField(default=uuid4, unique=True, editable=False)
    user = models.ForeignKey(
        DataspaceUser, on_delete=models.CASCADE, related_name="mfa_codes"
    )
    code = models.CharField(max_length=6)
    attempts = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    last_sent_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"MFA session {self.session_token} for {self.user.email}"

    @property
    def is_expired(self) -> bool:
        elapsed = (timezone.now() - self.created_at).total_seconds()
        return elapsed > django_settings.MFA_CODE_EXPIRY_SECONDS

    @property
    def is_max_attempts_exceeded(self) -> bool:
        return self.attempts >= django_settings.MFA_MAX_ATTEMPTS

    @staticmethod
    def generate_code() -> str:
        return "".join(secrets.choice("0123456789") for _ in range(6))
