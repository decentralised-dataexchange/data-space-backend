"""
Django Admin configuration for the OAuth2 Clients app.

This module registers the following models with the Django admin interface:
    - OAuth2Clients: Stores OAuth2 client credentials and configurations
      used for API authentication and authorization.
    - OrganisationOAuth2Clients: Organisation-specific OAuth2 client records
      that link clients to their parent organisations.

Both models share a common admin class (OAuth2ClientsAdmin) that provides:
    - Enhanced list display with key client information
    - Filtering and search capabilities
    - Organised fieldsets for better data management
    - Permission controls based on user roles
"""

from django.contrib import admin
from django.http import HttpRequest

from .models import OAuth2Clients, OrganisationOAuth2Clients


@admin.register(OAuth2Clients)
@admin.register(OrganisationOAuth2Clients)
class OAuth2ClientsAdmin(admin.ModelAdmin[OAuth2Clients]):
    """
    Custom admin configuration for OAuth2 client models.

    This admin class provides enhanced management capabilities for OAuth2 clients
    including organised display, filtering, and role-based access control.

    Key features:
        - Displays essential client information in the list view
        - Allows inline editing of the is_active status
        - Groups fields into logical sections (Client Info, Credentials, etc.)
        - Restricts add permissions to superusers only
        - Allows organisation admins to edit only their own clients
    """

    # Display columns: Shows client name, ID, owning organisation, status, and creation date
    # for quick identification and status monitoring of OAuth2 clients
    list_display = ("name", "client_id", "organisation", "is_active", "created_at")

    # Filter options: Enables filtering by active status, creation date,
    # and organisation name to narrow down client lists in large deployments
    list_filter = ("is_active", "created_at", "organisation__name")

    # Search fields: Allows searching across client name, client ID,
    # organisation name, and description for quick client lookup
    search_fields = ("name", "client_id", "organisation__name", "description")

    # Read-only fields: Prevents modification of auto-generated credentials
    # and timestamps to maintain data integrity and security
    readonly_fields = ("client_id", "client_secret", "created_at", "updated_at")

    # Editable in list view: Allows quick toggling of is_active status
    # directly from the list view without entering the detail page
    list_editable = ("is_active",)

    # Fieldsets: Organises form fields into logical sections for better UX
    # - Client Information: Basic identification fields
    # - Credentials: Sensitive auth data (collapsed by default for security)
    # - Status: Active/inactive toggle
    # - Timestamps: Audit trail information (collapsed by default)
    fieldsets = (
        ("Client Information", {"fields": ("name", "description", "organisation")}),
        (
            "Credentials",
            {"fields": ("client_id", "client_secret"), "classes": ("collapse",)},
        ),
        ("Status", {"fields": ("is_active",)}),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    def has_add_permission(self, request: HttpRequest) -> bool:
        """
        Determine if the user can create new OAuth2 clients.

        Only superusers are allowed to add OAuth clients from the admin interface.
        This restriction ensures that client credential generation is controlled
        and prevents unauthorized creation of authentication credentials.

        Args:
            request: The current HTTP request containing user information.

        Returns:
            bool: True if user is a superuser, False otherwise.
        """
        return bool(getattr(request.user, "is_superuser", False))

    def has_change_permission(
        self, request: HttpRequest, obj: OAuth2Clients | None = None
    ) -> bool:
        """
        Determine if the user can modify an OAuth2 client.

        Implements role-based access control:
            - Superusers can edit all OAuth2 clients
            - Organisation admins can only edit clients belonging to their organisation

        Args:
            request: The current HTTP request containing user information.
            obj: The OAuth2Clients instance being edited, or None for list view.

        Returns:
            bool: True if user has permission to edit, False otherwise.
        """
        if getattr(request.user, "is_superuser", False):
            return True
        if obj and hasattr(request.user, "organisation"):
            return bool(obj.organisation == request.user.organisation)
        return False
