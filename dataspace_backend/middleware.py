"""
Custom Django middleware for the Data Space Backend application.

This module contains middleware classes that process requests before they
reach views and/or process responses before they are returned to clients.

The primary middleware in this module handles URL normalization for non-GET
requests, solving a common Django issue with trailing slashes and request
body preservation.
"""

from typing import Callable

from django.http import HttpRequest, HttpResponse
from django.urls import Resolver404, resolve


class NonGetAppendSlashMiddleware:
    """
    Middleware to normalize URLs by handling trailing slashes for non-GET requests.

    Problem Being Solved:
        Django's built-in CommonMiddleware with APPEND_SLASH=True automatically
        redirects requests without trailing slashes to slash-terminated URLs.
        However, for non-safe HTTP methods (POST, PUT, PATCH, DELETE), this
        redirect causes issues because:
        1. The redirect loses the request body
        2. Django raises RuntimeError to prevent silent data loss

    Solution:
        Instead of redirecting, this middleware rewrites the request path
        in-place before it reaches the URL dispatcher. This preserves the
        request body while still routing to the correct view.

    Behavior:
        - For safe methods (GET, HEAD, OPTIONS, TRACE): Does nothing,
          allowing Django's default APPEND_SLASH redirect behavior.
        - For non-safe methods (POST, PUT, PATCH, DELETE):
          - If the path doesn't end with "/" and the slash-terminated
            version resolves to a valid view, rewrites the path.
          - If the path ends with "/" and the non-slash version resolves,
            rewrites to remove the slash (for consistency).

    Usage:
        Add to MIDDLEWARE in settings.py, preferably before CommonMiddleware:
        MIDDLEWARE = [
            'dataspace_backend.middleware.NonGetAppendSlashMiddleware',
            'django.middleware.common.CommonMiddleware',
            ...
        ]
    """

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        """
        Initialize the middleware with the next handler in the chain.

        Args:
            get_response: The next middleware or view in the request chain.
                         Called to continue processing the request.
        """
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        """
        Process the request, potentially rewriting the path for non-safe methods.

        This method is called for every request. It checks if the request uses
        a non-safe HTTP method and, if so, attempts to normalize the URL path
        by adding or removing a trailing slash based on URL resolution.

        Args:
            request: The incoming HTTP request object.

        Returns:
            The HTTP response from downstream middleware/views.
        """
        # Only operate on non-safe methods that would fail with APPEND_SLASH redirect
        # Safe methods (GET, HEAD, OPTIONS, TRACE) can be safely redirected by
        # Django's CommonMiddleware since they don't carry request bodies
        if request.method not in ("GET", "HEAD", "OPTIONS", "TRACE"):
            # Get the current request path
            path_info = request.path_info or ""

            if path_info and not path_info.endswith("/"):
                # Path doesn't have trailing slash - try adding one
                candidate_path = f"{path_info}/"

                try:
                    # Check if the slash-terminated path resolves to a view
                    resolve(candidate_path)
                except Resolver404:
                    # Candidate path doesn't resolve - keep original path
                    pass
                else:
                    # Candidate path resolves successfully - rewrite the request path
                    # This allows the request to be routed correctly without a redirect
                    request.path_info = candidate_path
                    request.META["PATH_INFO"] = candidate_path

        # Continue to the next middleware/view in the chain
        return self.get_response(request)
