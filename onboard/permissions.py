"""
Custom Permission Classes for Dataspace API.

This module defines custom permission classes used throughout the Dataspace API
to control access to resources based on ownership and request type.

These permissions extend Django REST Framework's base permission classes and
implement business rules for object-level access control.

Business Logic:
    - Users can view certain resources without restrictions (HEAD, OPTIONS)
    - Modification of resources is restricted to the owner of that resource
    - Ownership is determined by matching the object's email with the request user's email

Usage:
    Apply these permission classes to views or viewsets:

        class MyViewSet(viewsets.ModelViewSet):
            permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]
"""

from typing import Any

from rest_framework import permissions


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission that restricts write access to object owners only.

    This permission class implements a common access control pattern where:
    - Metadata requests (HEAD, OPTIONS) are allowed for all authenticated users
    - Write operations (POST, PUT, PATCH, DELETE) are only allowed if the
      requesting user owns the object

    Ownership is determined by comparing the email address stored on the object
    with the email address of the authenticated user making the request.

    This is useful for resources like user profiles, personal settings, or
    any model where users should only be able to modify their own records.

    Attributes:
        Inherits all attributes from permissions.BasePermission.

    Note:
        This permission class only handles object-level permissions. View-level
        permissions (like requiring authentication) should be handled by other
        permission classes used in conjunction with this one.

    Example:
        class UserProfileViewSet(viewsets.ModelViewSet):
            queryset = UserProfile.objects.all()
            permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]
    """

    def has_object_permission(self, request: Any, view: Any, obj: Any) -> bool:
        """
        Check if the request should be permitted for the given object.

        This method is called by DRF when checking object-level permissions,
        typically during retrieve, update, partial_update, and destroy actions.

        The permission logic follows these rules:
        1. HEAD and OPTIONS requests are always allowed (metadata/CORS preflight)
        2. All other requests require the user to be the owner of the object

        Args:
            request: The incoming HTTP request object. Contains the authenticated
                     user (request.user) and the HTTP method (request.method).
            view: The view instance handling the request. Not used in this
                  implementation but required by the BasePermission interface.
            obj: The object being accessed. Must have an 'email' attribute that
                 identifies the owner of the object.

        Returns:
            bool: True if the request is permitted, False otherwise.
                  - Returns True for HEAD and OPTIONS requests
                  - Returns True if obj.email matches request.user.email
                  - Returns False otherwise (denies write access to non-owners)

        Business Rules:
            - HEAD requests: Allowed (typically used for checking resource existence)
            - OPTIONS requests: Allowed (used for CORS preflight and API discovery)
            - GET requests: Requires ownership (unlike typical read-only patterns)
            - POST/PUT/PATCH/DELETE: Requires ownership

        Note:
            Unlike the standard DRF IsAuthenticatedOrReadOnly permission, this class
            does NOT allow unrestricted GET requests. GET requests also require
            ownership. Only HEAD and OPTIONS are truly "read-only" here.
        """
        # Allow metadata requests without ownership check
        # HEAD: Used to check if a resource exists without fetching the body
        # OPTIONS: Used for CORS preflight requests and API capability discovery
        if request.method in ("HEAD", "OPTIONS"):
            return True

        # For all other methods (GET, POST, PUT, PATCH, DELETE),
        # verify that the requesting user owns the object
        # Ownership is determined by matching email addresses
        return bool(obj.email == request.user.email)
