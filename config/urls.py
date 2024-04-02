from django.urls import path, include
from .views import DataSourceView, DataSourceCoverImageView, DataSourceLogoImageView, AdminView, DataSourceVerificationView
from connection.views import DISPConnectionView, DISPConnectionsView
from data_disclosure_agreement.views import DataDisclosureAgreementsView

urlpatterns = [
    path("data-source/", DataSourceView.as_view(), name="data_source"),
    path("data-source/coverimage/",
         DataSourceCoverImageView.as_view(), name="cover_image"),
    path("data-source/logoimage/",
         DataSourceLogoImageView.as_view(), name="logo_image"),
    path("admin/",
         AdminView.as_view(), name="admin"),
    path("data-source/verification/",
         DataSourceVerificationView.as_view(), name="verification"),
    path("data-source/connection/",
         DISPConnectionView.as_view(), name="connection"),
    path("data-source/connections/",
         DISPConnectionsView.as_view(), name="connection"),
    path("data-disclosure-agreement", include("data_disclosure_agreement.urls")),
    path("data-disclosure-agreements/", DataDisclosureAgreementsView.as_view(),
         name="data_disclosure_agreements"),
]
