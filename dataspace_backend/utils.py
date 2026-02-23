"""
General utility functions for the Data Space Backend application.

This module provides reusable helper functions for common operations across
the application, including:
- Generic model retrieval with error handling (returning 400 responses on failure)
- Pagination utilities for querysets and lists
- Convenience wrappers for retrieving DataSource and Organisation instances

These utilities reduce code duplication and standardize error handling patterns
throughout the codebase.
"""

from __future__ import annotations

from typing import Any, TypeVar

from django.db.models import Model, QuerySet
from django.http import HttpRequest, JsonResponse
from rest_framework import status

from config.models import DataSource

# TypeVar bound to Django Model for generic type hints in model retrieval functions
T = TypeVar("T", bound=Model)


def get_model_by_admin_or_400(
    model: type[T], user: Any
) -> tuple[T | None, JsonResponse | None]:
    """
    Retrieve a model instance where the given user is the admin.

    This function provides a standardized way to fetch model instances that have
    an 'admin' foreign key relationship, returning a 400 Bad Request response
    if the instance is not found.

    Args:
        model: The Django model class to query (must have an 'admin' field).
        user: The user instance to match against the model's admin field.

    Returns:
        A tuple containing:
        - The model instance if found, or None if not found.
        - None if found, or a JsonResponse with 400 status if not found.

    Example:
        datasource, error = get_model_by_admin_or_400(DataSource, request.user)
        if error:
            return error
        # Use datasource safely here
    """
    try:
        return model.objects.get(admin=user), None
    except model.DoesNotExist:
        return None, JsonResponse(
            {"error": "Not found"}, status=status.HTTP_400_BAD_REQUEST
        )


def get_instance_or_400(
    model: type[T], pk: Any, error_message: str
) -> tuple[T | None, JsonResponse | None]:
    """
    Retrieve a model instance by its primary key.

    This function provides a standardized way to fetch model instances by ID,
    returning a 400 Bad Request response if the instance is not found.

    Args:
        model: The Django model class to query.
        pk: The primary key value to look up.
        error_message: The error message to include in the JSON response if not found.

    Returns:
        A tuple containing:
        - The model instance if found, or None if not found.
        - None if found, or a JsonResponse with 400 status if not found.

    Example:
        organisation, error = get_instance_or_400(Organisation, org_id, "Organisation not found")
        if error:
            return error
        # Use organisation safely here
    """
    try:
        return model.objects.get(pk=pk), None
    except model.DoesNotExist:
        return None, JsonResponse(
            {"error": error_message}, status=status.HTTP_400_BAD_REQUEST
        )


def paginate_queryset(
    queryset: QuerySet[Any] | list[Any], request: HttpRequest
) -> tuple[QuerySet[Any] | list[Any], dict[str, Any]]:
    """
    Apply offset-based pagination to a queryset or list.

    This function extracts pagination parameters from the request's query string
    and returns a sliced subset of the data along with pagination metadata.
    It handles invalid or missing parameters gracefully with sensible defaults.

    Args:
        queryset: A Django QuerySet or Python list to paginate.
        request: The HTTP request containing 'offset' and 'limit' query parameters.

    Returns:
        A tuple containing:
        - The paginated slice of the queryset/list.
        - A dictionary with pagination metadata including:
            - currentPage: The current page number (1-indexed).
            - totalItems: Total number of items in the original dataset.
            - totalPages: Total number of pages available.
            - limit: The number of items per page (clamped to 1-100).
            - hasPrevious: Boolean indicating if there's a previous page.
            - hasNext: Boolean indicating if there's a next page.

    Notes:
        - Default offset is 0 (start from beginning).
        - Default limit is 10 items per page.
        - Limit is clamped between 1 and 100 to prevent abuse.
        - Offset is clamped to non-negative values.
    """
    # Extract pagination parameters from query string
    offset_str = request.GET.get("offset")
    limit_str = request.GET.get("limit")

    # Parse offset with fallback to 0 for invalid/missing values
    try:
        offset = int(offset_str)  # type: ignore[arg-type]
    except (ValueError, TypeError):
        offset = 0

    # Parse limit with fallback to 10 for invalid/missing values
    try:
        limit = int(limit_str)  # type: ignore[arg-type]
    except (ValueError, TypeError):
        limit = 10

    # Calculate total items - handle both QuerySet and list types
    if isinstance(queryset, list):
        total_items: int = len(queryset)
    else:
        total_items = queryset.count()

    # Sanitize pagination parameters to prevent invalid values
    # Offset must be non-negative, limit must be between 1 and 100
    offset = max(offset, 0)
    limit = max(1, min(limit, 100))

    # Apply pagination slice to the queryset/list
    queryset = queryset[offset : offset + limit]

    # Calculate current page number (1-indexed for API consumers)
    current_page = (offset // limit) + 1

    # Build pagination metadata for response
    pagination_data: dict[str, Any] = {
        "currentPage": current_page,
        "totalItems": total_items,
        # Ceiling division to calculate total pages
        "totalPages": (total_items + limit - 1) // limit,
        "limit": limit,
        "hasPrevious": offset > 0,
        "hasNext": offset + limit < total_items,
    }

    return queryset, pagination_data


def get_datasource_or_400(
    user: Any,
) -> tuple[DataSource | None, JsonResponse | None]:
    """
    Retrieve the DataSource instance where the given user is the admin.

    This is a convenience wrapper around get_model_by_admin_or_400 specifically
    for DataSource lookups, commonly used in config-related views.

    Args:
        user: The user instance to match against the DataSource's admin field.

    Returns:
        A tuple containing:
        - The DataSource instance if found, or None if not found.
        - None if found, or a JsonResponse with 400 status and
          generic "Not found" message if not found.
    """
    return get_model_by_admin_or_400(DataSource, user)


def get_organisation_or_400(user: Any) -> tuple[Any, JsonResponse | None]:
    """
    Retrieve the Organisation instance where the given user is the admin.

    This is a convenience wrapper around get_model_by_admin_or_400 specifically
    for Organisation lookups, commonly used in organisation-related views.

    Note:
        The Organisation model is imported locally to avoid circular imports,
        as the organisation app may depend on this utils module.

    Args:
        user: The user instance to match against the Organisation's admin field.

    Returns:
        A tuple containing:
        - The Organisation instance if found, or None if not found.
        - None if found, or a JsonResponse with 400 status and
          generic "Not found" message if not found.
    """
    # Local import to avoid circular dependency between utils and organisation app
    from organisation.models import Organisation

    return get_model_by_admin_or_400(Organisation, user)
