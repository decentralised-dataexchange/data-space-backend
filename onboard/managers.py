"""
Custom User Manager for Dataspace Authentication.

This module provides a custom user manager that extends Django's BaseUserManager
to support email-based authentication instead of the default username-based system.

The DataspaceUserManager implements the required methods for creating regular users
and superusers, with email as the primary identifier for authentication.

Business Logic:
    - Email addresses are used as unique identifiers (replacing usernames)
    - All email addresses are normalized to lowercase domain for consistency
    - Superusers automatically receive staff, superuser, and active status
    - Password handling delegates to Django's secure password hashing

Usage:
    This manager should be assigned to the DataspaceUser model's `objects` attribute:

        class DataspaceUser(AbstractUser):
            objects = DataspaceUserManager()
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from django.contrib.auth.base_user import BaseUserManager

# TYPE_CHECKING is used to avoid circular imports at runtime
# while still providing type hints for static analysis tools
if TYPE_CHECKING:
    from onboard.models import DataspaceUser


class DataspaceUserManager(BaseUserManager):  # type: ignore[type-arg]
    """
    Custom user model manager for email-based authentication.

    This manager replaces the default username-based authentication with
    email-based authentication. It provides methods to create both regular
    users and superusers with proper validation and default settings.

    The manager ensures that:
        - All users have a valid email address
        - Email addresses are normalized for consistency
        - Passwords are properly hashed using Django's security mechanisms
        - Superusers have the required permission flags set

    Attributes:
        Inherits all attributes from BaseUserManager.

    Type Parameters:
        DataspaceUser: The custom user model this manager operates on.
    """

    def create_user(
        self, email: str, password: str | None, **extra_fields: Any
    ) -> "DataspaceUser":
        """
        Create and save a regular user with the given email and password.

        This method handles the standard user creation workflow:
        1. Validates that an email address is provided
        2. Normalizes the email (lowercases the domain portion)
        3. Creates the user instance with any extra fields
        4. Sets the password using Django's secure hashing
        5. Saves and returns the user

        Args:
            email: The user's email address. This will be used as the unique
                   identifier for authentication. Must not be empty.
            password: The user's password in plain text. Will be hashed before
                      storage. Can be None for users who authenticate via
                      external providers (OAuth, SSO, etc.).
            **extra_fields: Additional fields to set on the user model, such as
                            first_name, last_name, is_active, etc.

        Returns:
            DataspaceUser: The newly created and saved user instance.

        Raises:
            ValueError: If the email parameter is empty or None.

        Example:
            user = DataspaceUser.objects.create_user(
                email='user@example.com',
                password='securepassword123',
                first_name='John'
            )
        """
        # Email is required as it serves as the unique identifier
        if not email:
            raise ValueError("The Email must be set")

        # Normalize email: lowercase the domain part for consistency
        # e.g., "User@EXAMPLE.COM" becomes "User@example.com"
        email = self.normalize_email(email)

        # Create the user model instance with email and any extra fields
        user = self.model(email=email, **extra_fields)

        # Use set_password to properly hash the password
        # This also handles None passwords for external auth providers
        user.set_password(password)

        # Persist the user to the database
        user.save()

        return user

    def create_superuser(
        self, email: str, password: str | None, **extra_fields: Any
    ) -> "DataspaceUser":
        """
        Create and save a superuser with the given email and password.

        Superusers are administrative accounts with full system access.
        This method ensures that superuser accounts have the required
        permission flags (is_staff, is_superuser, is_active) properly set.

        The method uses setdefault to set required flags, allowing them
        to be overridden if explicitly provided (though this is validated).

        Args:
            email: The superuser's email address. Used as the unique
                   identifier for authentication.
            password: The superuser's password in plain text. Will be
                      hashed before storage.
            **extra_fields: Additional fields to set on the user model.
                            Note that is_staff, is_superuser, and is_active
                            will be defaulted to True if not provided.

        Returns:
            DataspaceUser: The newly created and saved superuser instance.

        Raises:
            ValueError: If email is empty, or if is_staff or is_superuser
                        are explicitly set to False.

        Example:
            admin = DataspaceUser.objects.create_superuser(
                email='admin@example.com',
                password='adminpassword123'
            )
        """
        # Set default permission flags for superuser accounts
        # Using setdefault allows these to be pre-set in extra_fields if needed
        extra_fields.setdefault("is_staff", True)  # Required for admin site access
        extra_fields.setdefault("is_superuser", True)  # Grants all permissions
        extra_fields.setdefault("is_active", True)  # Account must be active

        # Validate that superuser flags are not explicitly set to False
        # This prevents accidental creation of non-functional superuser accounts
        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        # Delegate to create_user for the actual user creation
        return self.create_user(email, password, **extra_fields)
