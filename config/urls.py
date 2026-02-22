from django.urls import include, path
from django.views.decorators.csrf import csrf_exempt

from config.views import AdminReset, PasswordChangeView
from connection.views import DISPConnectionsView
from data_disclosure_agreement.views import (
    DataDisclosureAgreementTemplatesView,
)

from .views import (
    AdminView,
    DataSourceCoverImageView,
    DataSourceLogoImageView,
    DataSourceOpenApiUrlView,
    DataSourceVerificationView,
    DataSourceView,
    VerificationTemplateView,
)

urlpatterns = [
    path("data-source/", DataSourceView.as_view(), name="data_source"),
    path(
        "data-source/coverimage/",
        DataSourceCoverImageView.as_view(),
        name="cover_image",
    ),
    path(
        "data-source/logoimage/", DataSourceLogoImageView.as_view(), name="logo_image"
    ),
    path("admin/", AdminView.as_view(), name="admin"),
    path(
        "data-source/verification/",
        DataSourceVerificationView.as_view(),
        name="verification",
    ),
    path("connections/", DISPConnectionsView.as_view(), name="connections"),
    path("connection", include("connection.urls")),
    path("data-disclosure-agreement", include("data_disclosure_agreement.urls")),
    path(
        "data-disclosure-agreements/",
        DataDisclosureAgreementTemplatesView.as_view(),
        name="data_disclosure_agreements",
    ),
    path(
        "verification/templates",
        VerificationTemplateView.as_view(),
        name="verification_templates",
    ),
    path("open-api/url", DataSourceOpenApiUrlView.as_view(), name="open_api_url"),
    path(
        "admin/reset-password/",
        csrf_exempt(PasswordChangeView.as_view()),
        name="password_reset",
    ),
    path("admin/reset/", AdminReset, name="reset_connections_and_verifications"),
    path("organisation", include("organisation.urls")),
]
