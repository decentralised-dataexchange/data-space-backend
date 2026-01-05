from django.contrib.admin import AdminSite
from django.contrib.auth.forms import AuthenticationForm


# Register your models here.
class MyAdminSite(AdminSite):
    """
    App-specific admin site implementation
    """

    login_form = AuthenticationForm

    site_header = "CRANE d-HDSI Data Marketplace Administration"

    def has_permission(self, request):
        """
        Checks if the current user has access.
        """
        return request.user.is_active


myadminsite = MyAdminSite(name="myadmin")
