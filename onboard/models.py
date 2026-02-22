"""
Onboard Models Module

This module defines the user model for the data space platform. It provides
custom user authentication using email as the primary identifier instead of
username, which is the standard approach for modern web applications.
"""

from __future__ import annotations

from uuid import uuid4

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

    # Specifies that email is used as the unique identifier for authentication
    USERNAME_FIELD: str = "email"

    # No additional required fields beyond email (password is handled by AbstractBaseUser)
    REQUIRED_FIELDS: "list[str]" = []  # type: ignore[misc]

    # Custom manager that handles user creation with email as the identifier
    objects: "DataspaceUserManager" = DataspaceUserManager()  # type: ignore[misc]

    def __str__(self) -> str:
        return str(self.email)
