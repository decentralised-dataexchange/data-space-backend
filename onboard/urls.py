from django.urls import include, path
from django.views.decorators.csrf import csrf_exempt
from rest_framework_simplejwt.views import (TokenObtainPairView,
                                            TokenRefreshView)

from .views import CreateUserView, UserDetail,UserLogin, CreateUserAndOrganisationView, SectorView, CodeOfConductView

urlpatterns = [
    path("extras/", include("rest_auth.urls")),
    path("register/", csrf_exempt(CreateUserAndOrganisationView.as_view())),
    path("login/", UserLogin.as_view(), name="token_obtain_pair"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("sectors/", SectorView.as_view(), name="sectors"),
    path("code-of-conduct/", CodeOfConductView.as_view(), name="code_of_conduct"),
]
