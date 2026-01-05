from django.contrib import admin

from .models import OAuth2Clients, OrganisationOAuth2Clients


@admin.register(OAuth2Clients)
@admin.register(OrganisationOAuth2Clients)
class OAuth2ClientsAdmin(admin.ModelAdmin):
    list_display = ["name", "client_id", "organisation", "is_active", "created_at"]
    list_filter = ["is_active", "created_at", "organisation__name"]
    search_fields = ["name", "client_id", "organisation__name", "description"]
    readonly_fields = ["client_id", "client_secret", "created_at", "updated_at"]
    list_editable = ["is_active"]

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

    def has_add_permission(self, request):
        """Only superusers can add OAuth clients from admin"""
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        """Superusers can edit all, organisation admins can edit their own"""
        if request.user.is_superuser:
            return True
        if obj and hasattr(request.user, "organisation"):
            return obj.organisation == request.user.organisation
        return False
