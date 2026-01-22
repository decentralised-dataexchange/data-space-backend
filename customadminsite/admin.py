from django.contrib.admin import AdminSite
from django.contrib.auth.forms import AuthenticationForm
from django.http import HttpRequest


# Register your models here.
class MyAdminSite(AdminSite):
    """
    App-specific admin site implementation
    """

    login_form = AuthenticationForm

    site_header = "CRANE d-HDSI Data Marketplace Administration"

    def has_permission(self, request: HttpRequest) -> bool:
        """
        Checks if the current user has access.
        """
        return bool(request.user.is_active)


myadminsite: MyAdminSite = MyAdminSite(name="myadmin")
