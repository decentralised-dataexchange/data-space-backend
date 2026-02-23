"""
Django Admin Configuration for Onboard Module.

This module registers the DataspaceUser model with the Django admin interface,
providing a customized admin experience for managing user accounts in the
data space platform. The custom admin class extends Django's built-in UserAdmin
to handle email-based authentication instead of username-based authentication.

Registered Models:
    - DataspaceUser: Custom user model for data space platform authentication
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import UserChangeForm, UserCreationForm

from onboard.models import DataspaceUser, MFACode


class CustomUserCreationForm(UserCreationForm):  # type: ignore[type-arg]
    """
    Custom form for creating new DataspaceUser instances in the admin.

    This form extends Django's UserCreationForm to use email as the primary
    identifier instead of username, aligning with the DataspaceUser model's
    email-based authentication approach.
    """

    class Meta:
        model = DataspaceUser
        # Only require email field for user creation (password fields are inherited)
        fields = ("email",)


class CustomUserChangeForm(UserChangeForm):  # type: ignore[type-arg]
    """
    Custom form for modifying existing DataspaceUser instances in the admin.

    This form extends Django's UserChangeForm to use email as the primary
    identifier, ensuring consistency with the custom user model's design.
    """

    class Meta:
        model = DataspaceUser
        # Only include email field for user modification (other fields handled by fieldsets)
        fields = ("email",)


class DataspaceUserAdmin(BaseUserAdmin):  # type: ignore[type-arg]
    """
    Custom admin configuration for the DataspaceUser model.

    This admin class provides a tailored interface for managing data space users,
    with email-based authentication support. It customizes the display, filtering,
    and form layouts to work with the custom user model that uses email instead
    of username as the primary identifier.

    Key Customizations:
        - Uses email as the primary user identifier
        - Custom creation and change forms for email-based authentication
        - Organized fieldsets for logical grouping of user attributes
        - Horizontal filter widget for managing groups and permissions
    """

    # Custom forms for user creation and modification with email-based authentication
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = DataspaceUser

    # Enable horizontal filter widget for many-to-many relationships
    # Makes it easier to manage user groups and permissions
    filter_horizontal = ("groups", "user_permissions")

    # Columns displayed in the user list view
    # Shows essential user information at a glance
    list_display = (
        "email",  # Primary identifier for the user
        "is_staff",  # Indicates admin site access
        "is_active",  # Indicates if user account is active
        "name",  # Display name of the user
    )

    # Sidebar filters for narrowing down user list
    # Allows filtering by key user attributes
    list_filter = (
        "email",  # Filter by email address
        "is_staff",  # Filter by staff status
        "is_active",  # Filter by active status
        "name",  # Filter by user name
    )

    # Fieldsets for the user edit page
    # Organizes fields into logical sections
    fieldsets = (
        # Primary credentials section
        (None, {"fields": ("email", "password")}),
        # Permissions and metadata section
        (
            "Permissions",
            {
                "fields": (
                    "is_staff",  # Staff status for admin access
                    "is_active",  # Account activation status
                    "name",  # User's display name
                    "user_permissions",  # Include user permissions field
                )
            },
        ),
    )

    # Fieldsets for the user creation page
    # Provides a wide layout for new user registration
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),  # Use wide layout for better visibility
                "fields": (
                    "email",  # Required email for authentication
                    "password1",  # Password entry
                    "password2",  # Password confirmation
                    "is_staff",  # Optional staff status
                    "is_active",  # Optional active status
                    "name",  # Optional display name
                    "user_permissions",  # Include user permissions field
                ),
            },
        ),
    )

    # Fields available for searching users
    # Enables quick lookup by email address
    search_fields = ("email",)

    # Default ordering for the user list
    # Users are sorted alphabetically by email
    ordering = ("email",)


# Register the DataspaceUser model with its custom admin configuration
admin.site.register(DataspaceUser, DataspaceUserAdmin)


@admin.register(MFACode)
class MFACodeAdmin(admin.ModelAdmin):  # type: ignore[type-arg]
    list_display = ("user", "session_token", "created_at", "is_used", "attempts")
    list_filter = ("is_used",)
    search_fields = ("user__email",)
    readonly_fields = ("session_token", "code", "created_at", "last_sent_at")
