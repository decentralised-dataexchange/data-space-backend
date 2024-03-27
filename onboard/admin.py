from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import UserChangeForm, UserCreationForm

from onboard.models import DataspaceUser


class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = DataspaceUser
        fields = ("email",)


class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = DataspaceUser
        fields = ("email",)


class DataspaceUserAdmin(BaseUserAdmin):
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = DataspaceUser
    list_display = (
        "email",
        "is_staff",
        "is_active",
        "name",
    )
    list_filter = (
        "email",
        "is_staff",
        "is_active",
        "name",
    )
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (
            "Permissions",
            {
                "fields": (
                    "is_staff",
                    "is_active",
                    "name",
                )
            },
        ),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "password1",
                    "password2",
                    "is_staff",
                    "is_active",
                    "name",
                ),
            },
        ),
    )
    search_fields = ("email",)
    ordering = ("email",)


admin.site.register(DataspaceUser, DataspaceUserAdmin)
