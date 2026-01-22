"""
Django Admin Configuration for Data Disclosure Agreement Module.

This module registers Data Disclosure Agreement (DDA) models with a custom admin site.
DDAs are legal agreements that govern how data can be shared between parties in the
data space. The admin interface provides management capabilities for agreement
templates used to create standardized disclosure agreements.

Registered Models:
    - DataDisclosureAgreementTemplate: Templates for creating standardized DDAs

Note:
    Models are registered with 'myadminsite' (custom admin site) rather than
    the default Django admin site, allowing for separate admin interfaces
    or customized branding.
"""

from typing import Callable

from django.contrib import admin
from django.http import HttpRequest

from customadminsite.admin import myadminsite

from .models import DataDisclosureAgreementTemplate


class DataDisclosureAgreementAdmin(admin.ModelAdmin[DataDisclosureAgreementTemplate]):
    """
    Custom admin configuration for the DataDisclosureAgreementTemplate model.

    This admin class provides a tailored interface for managing DDA templates,
    displaying key information about each template including its purpose,
    status, and version information. Templates are the foundation for creating
    individual data disclosure agreements between parties.

    Key Features:
        - Displays template identification and purpose
        - Shows agreement status and version tracking
        - Integrated with custom admin site for specialized access control
    """

    # Columns displayed in the template list view
    # Shows essential template information for quick identification
    list_display = (
        "templateId",  # Unique identifier for the template
        "purpose",  # Description of what the agreement is for
        "status",  # Current status (e.g., draft, active, deprecated)
        "createdAt",  # Timestamp when template was created
        "isLatestVersion",  # Flag indicating if this is the most recent version
    )

    def get_list_display(
        self, request: HttpRequest
    ) -> tuple[str | Callable[[DataDisclosureAgreementTemplate], str | bool], ...]:
        """
        Return the list of fields to display in the admin list view.

        This method provides the list_display configuration and can be
        overridden in subclasses to customize the display based on the
        request context (e.g., user permissions).

        Args:
            request: The current HTTP request

        Returns:
            Tuple of field names or callable functions for list display
        """
        return self.list_display


# DataDisclosureAgreement instance registration is disabled
# Individual agreement records are typically managed through the API
# myadminsite.register(DataDisclosureAgreement, DataDisclosureAgreementAdmin)

# Register DataDisclosureAgreementTemplate with custom admin site
# Templates are managed through the custom admin interface for DDA workflows
myadminsite.register(DataDisclosureAgreementTemplate, DataDisclosureAgreementAdmin)
