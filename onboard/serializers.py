"""
Serializers for user onboarding and authentication in the Data Space platform.

This module provides serializers for:
- User registration with secure password handling
- User profile retrieval and updates
- Authentication token responses with embedded user data
- Listing users in the data space

These serializers support the onboarding flow where users register,
authenticate, and manage their profiles within the data space ecosystem.
"""

from __future__ import annotations

from typing import Any

from rest_framework import serializers
from rest_framework.authtoken.models import Token

from .models import DataspaceUser


class RegisterDataspaceUserSerializer(serializers.ModelSerializer):  # type: ignore[type-arg]
    """
    Serializer for registering new users in the Data Space platform.

    Handles the creation of new DataspaceUser accounts with proper password
    hashing. The password field is write-only to ensure it is never exposed
    in API responses.

    Fields:
        id: Unique identifier for the user (read-only, auto-generated)
        email: User's email address, used as the primary login identifier
        password: User's password (write-only, hashed before storage)
        name: User's display name
    """

    # Password is write-only to prevent exposure in API responses
    password = serializers.CharField(write_only=True)

    class Meta:
        model = DataspaceUser
        fields = ["id", "email", "password", "name"]

    def create(self, validated_data: dict[str, Any]) -> DataspaceUser:
        """
        Create a new DataspaceUser with properly hashed password.

        Uses the custom create_user method from the user manager to ensure
        the password is securely hashed before storage, rather than storing
        it in plain text.

        Args:
            validated_data: Dictionary containing email, password, and name

        Returns:
            The newly created DataspaceUser instance
        """
        # Use create_user method to handle password hashing
        user: DataspaceUser = DataspaceUser.objects.create_user(**validated_data)
        return user


class DataspaceUserSerializer(serializers.ModelSerializer):  # type: ignore[type-arg]
    """
    Serializer for retrieving and updating DataspaceUser profiles.

    Used for read operations (GET) to display user information and for
    partial updates (PATCH) to modify user profile fields. Note that
    password updates should be handled through a separate endpoint with
    proper verification.

    Fields:
        id: Unique identifier for the user (read-only)
        email: User's email address (read-only in updates)
        name: User's display name (editable)
    """

    class Meta:
        model = DataspaceUser
        fields = ["id", "email", "name"]

    def update(
        self, instance: DataspaceUser, validated_data: dict[str, Any]
    ) -> DataspaceUser:
        """
        Update a DataspaceUser's profile information.

        Currently only supports updating the 'name' field. Email changes
        would require additional verification logic and are not supported
        through this serializer.

        Args:
            instance: The existing DataspaceUser to update
            validated_data: Dictionary containing fields to update

        Returns:
            The updated DataspaceUser instance
        """
        # Update only the "name" field if provided in the request
        instance.name = validated_data.get("name", instance.name)
        instance.save()
        return instance


class CustomTokenSerializer(serializers.ModelSerializer):  # type: ignore[type-arg]
    """
    Serializer for authentication token responses with embedded user data.

    Extends the standard token serializer to include full user details
    alongside the authentication token. This allows clients to receive
    both the auth token and user profile in a single response after
    successful login.

    Fields:
        key: The authentication token string
        user: Nested user object with id, email, and name
    """

    # Embed full user details in the token response for client convenience
    user = DataspaceUserSerializer(many=False, read_only=True)

    class Meta:
        model = Token
        fields = ("key", "user")


class DataspaceUsersSerializer(serializers.ModelSerializer):  # type: ignore[type-arg]
    """
    Serializer for listing multiple DataspaceUser instances.

    Provides a read-only view of user information suitable for listing
    users in admin interfaces or user directories. Does not include
    sensitive information like passwords.

    Fields:
        id: Unique identifier for the user
        email: User's email address
        name: User's display name
    """

    class Meta:
        model = DataspaceUser
        fields = ["id", "email", "name"]
