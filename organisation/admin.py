"""
Django Admin Configuration for Organisation Module.

This module registers organisation-related models with the Django admin interface,
providing management capabilities for organisations participating in the data space.
It includes a custom admin class for CodeOfConduct with PDF upload functionality
that stores files directly in the database.

Registered Models:
    - Organisation: Core organisation entity in the data space
    - OrganisationIdentity: Identity credentials for organisations
    - OrganisationIdentityTemplate: Templates for organisation identity structures
    - Sector: Industry sectors for categorizing organisations
    - CodeOfConduct: PDF documents defining conduct rules with custom admin handling
"""

from __future__ import annotations

from django import forms
from django.contrib import admin
from django.http import HttpRequest

from organisation.models import (
    CodeOfConduct,
    Organisation,
    OrganisationIdentity,
    OrganisationIdentityTemplate,
    Sector,
)


class CodeOfConductAdminForm(forms.ModelForm):  # type: ignore[type-arg]
    """
    Custom form for managing CodeOfConduct instances in the admin.

    This form provides a file upload field for PDF documents and handles
    storing the file content directly in the database rather than on the
    filesystem. This approach ensures portability and simplifies backup/restore
    operations.

    Attributes:
        pdfFile: A FileField that accepts PDF uploads and stores content in database
    """

    # Custom file upload field for PDF documents
    # The uploaded file content will be stored in the database binary field
    pdfFile = forms.FileField(
        required=False,
        label="PDF File",
        help_text="Upload a PDF file. It will be stored in the database.",
    )

    class Meta:
        model = CodeOfConduct
        # Only expose the file upload and active status fields
        fields = ["pdfFile", "isActive"]

    def save(self, commit: bool = True) -> CodeOfConduct:
        """
        Save the CodeOfConduct instance with uploaded PDF content.

        Overrides the default save behavior to read the uploaded PDF file
        content and store it in the database binary field along with the
        original filename.

        Args:
            commit: If True, save the instance to the database immediately

        Returns:
            The saved or unsaved CodeOfConduct instance
        """
        instance: CodeOfConduct = super().save(commit=False)
        pdf_file = self.cleaned_data.get("pdfFile")
        # If a new PDF file was uploaded, read and store its content
        if pdf_file:
            instance.pdfContent = pdf_file.read()  # Store binary content in database
            instance.pdfFileName = pdf_file.name  # Preserve original filename
        if commit:
            instance.save()
        return instance


class CodeOfConductAdmin(admin.ModelAdmin):  # type: ignore[type-arg]
    """
    Custom admin configuration for the CodeOfConduct model.

    This admin class provides a specialized interface for managing Code of Conduct
    PDF documents. It uses a custom form for PDF upload and dynamically adjusts
    the displayed fields based on whether the user is creating a new record or
    editing an existing one.

    Key Features:
        - PDF file upload with database storage
        - Conditional field display for create vs edit views
        - Read-only audit fields (timestamps and generated ID)
    """

    # Use custom form with PDF upload functionality
    form = CodeOfConductAdminForm

    # Columns displayed in the list view
    # Shows document identification and status information
    list_display = (
        "id",  # Unique identifier for the document
        "pdfFileName",  # Original filename of the uploaded PDF
        "isActive",  # Whether this code of conduct is currently active
        "createdAt",  # Timestamp when document was uploaded
        "updatedAt",  # Timestamp of last modification
    )

    # Sidebar filters for the list view
    # Allows filtering by active/inactive status
    list_filter = ("isActive",)

    # Fields that cannot be modified by admin users
    # These are system-generated or computed values
    readonly_fields = (
        "id",  # Auto-generated primary key
        "createdAt",  # Auto-set on creation
        "updatedAt",  # Auto-updated on save
        "pdfFileName",  # Set automatically from uploaded file
    )

    def get_fields(
        self, request: HttpRequest, obj: CodeOfConduct | None = None
    ) -> tuple[str, ...]:
        """
        Dynamically determine which fields to display in the admin form.

        When editing an existing CodeOfConduct, shows all fields including
        read-only metadata. When creating a new one, only shows the upload
        field and active status.

        Args:
            request: The current HTTP request
            obj: The CodeOfConduct instance being edited, or None for new records

        Returns:
            Tuple of field names to display in the form
        """
        if obj:
            # Editing existing record: show all fields including metadata
            return (
                "id",
                "pdfFile",
                "pdfFileName",
                "isActive",
                "createdAt",
                "updatedAt",
            )
        # Creating new record: only show essential input fields
        return ("pdfFile", "isActive")


# Register Organisation model with default admin configuration
# Provides basic CRUD operations for organisation management
admin.site.register(Organisation)

# Register OrganisationIdentity model with default admin configuration
# Manages identity credentials associated with organisations
admin.site.register(OrganisationIdentity)

# Register OrganisationIdentityTemplate model with default admin configuration
# Manages templates that define the structure of organisation identities
admin.site.register(OrganisationIdentityTemplate)

# Register Sector model with default admin configuration
# Manages industry sectors used to categorize organisations
admin.site.register(Sector)

# Register CodeOfConduct model with custom admin configuration
# Uses CodeOfConductAdmin for PDF upload and database storage functionality
admin.site.register(CodeOfConduct, CodeOfConductAdmin)
