from django.urls import include, path
from django.views.decorators.csrf import csrf_exempt
from rest_auth.views import PasswordChangeView
from rest_framework_simplejwt.views import (TokenObtainPairView,
                                            TokenRefreshView)

from .views import CreateUserView, UserDetail

urlpatterns = [
    path("extras/", include("rest_auth.urls")),
    path("register/", csrf_exempt(CreateUserView.as_view())),
    path("login/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("password/reset/", csrf_exempt(PasswordChangeView.as_view()), name="password_reset")
]
