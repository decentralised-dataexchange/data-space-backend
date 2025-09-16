from django.urls import path, include
from .views import OrganisationView, OrganisationCoverImageView, OrganisationLogoImageView, OrganisationIdentityView
from oAuth2Clients.views import OAuth2ClientsView
from software_statement.views import SoftwareStatementView

urlpatterns = [
    path("/", OrganisationView.as_view(), name="organisation"),
    path("/coverimage/",
        OrganisationCoverImageView.as_view(), name="organisation_cover_image"),
    path("/logoimage/",
        OrganisationLogoImageView.as_view(), name="logo_image"),
    path("/identity/",OrganisationIdentityView.as_view(), name="organisation_identity"),
    path("/oauth2-client", include("oAuth2Clients.urls")),
    path("/oauth2-clients/", OAuth2ClientsView.as_view(), name="oauth-clients"),
    path("/software-statement/",SoftwareStatementView.as_view(), name="organisation_software_statement"),
]