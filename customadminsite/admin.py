"""
Custom Admin Site Configuration for CRANE d-HDSI Data Marketplace.

This module provides a custom Django AdminSite implementation that extends
the default admin functionality with project-specific customizations.
The custom admin site is used throughout the application to provide a
consistent branded administration experience.

Key Customizations:
    - Custom site header branding for the Data Marketplace
    - Modified permission checking to allow any active user access
    - Standard Django authentication form for login

Registered Models:
    None - This module defines the admin site itself, not model registrations.
    Models are registered to this custom site from their respective app admin modules.

Usage:
    Import myadminsite from this module and use it to register models:
        from customadminsite.admin import myadminsite
        myadminsite.register(MyModel, MyModelAdmin)
"""

from django.contrib.admin import AdminSite
from django.contrib.auth.forms import AuthenticationForm
from django.http import HttpRequest


class MyAdminSite(AdminSite):
    """
    Custom admin site for the CRANE d-HDSI Data Marketplace application.

    This class extends Django's AdminSite to provide project-specific
    customizations for the administration interface. It overrides the
    default permission model to allow any authenticated active user
    to access the admin interface, rather than requiring staff status.

    Attributes:
        login_form: The authentication form used for admin login.
            Uses Django's standard AuthenticationForm.
        site_header: The text displayed at the top of admin pages.
            Branded for the CRANE d-HDSI Data Marketplace.

    Note:
        The relaxed permission model (allowing any active user) should be
        used in conjunction with proper object-level permissions in
        individual ModelAdmin classes to ensure data security.
    """

    # Use Django's standard authentication form for admin login
    login_form = AuthenticationForm

    # Custom branding for the admin site header
    site_header = "CRANE d-HDSI Data Marketplace Administration"

    def has_permission(self, request: HttpRequest) -> bool:
        """
        Check if the current user has permission to access the admin site.

        This method overrides the default AdminSite.has_permission() which
        requires both is_active and is_staff to be True. This implementation
        only checks if the user is active, allowing non-staff users to access
        the admin interface.

        Args:
            request: The HTTP request object containing user information.

        Returns:
            bool: True if the user is active, False otherwise.

        Warning:
            This permissive access control should be paired with appropriate
            object-level permissions in ModelAdmin classes to prevent
            unauthorized data access or modification.
        """
        return bool(request.user.is_active)


# Singleton instance of the custom admin site
# This instance should be used for all model registrations throughout the project
myadminsite: MyAdminSite = MyAdminSite(name="myadmin")
