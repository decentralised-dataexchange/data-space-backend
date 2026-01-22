from django.contrib import admin
from django.http import HttpRequest

from .models import OAuth2Clients, OrganisationOAuth2Clients


@admin.register(OAuth2Clients)
@admin.register(OrganisationOAuth2Clients)
class OAuth2ClientsAdmin(admin.ModelAdmin[OAuth2Clients]):
    list_display = ("name", "client_id", "organisation", "is_active", "created_at")
    list_filter = ("is_active", "created_at", "organisation__name")
    search_fields = ("name", "client_id", "organisation__name", "description")
    readonly_fields = ("client_id", "client_secret", "created_at", "updated_at")
    list_editable = ("is_active",)

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
        """Only superusers can add OAuth clients from admin"""
        return bool(getattr(request.user, "is_superuser", False))

    def has_change_permission(
        self, request: HttpRequest, obj: OAuth2Clients | None = None
    ) -> bool:
        """Superusers can edit all, organisation admins can edit their own"""
        if getattr(request.user, "is_superuser", False):
            return True
        if obj and hasattr(request.user, "organisation"):
            return bool(obj.organisation == request.user.organisation)
        return False
