from django.urls import path, include
from .views import OrganisationView, OrganisationCoverImageView, OrganisationLogoImageView, OrganisationIdentityView, CodeOfConductUpdateView
from oAuth2Clients.views import OAuth2ClientsView, OAuth2ClientView, OrganisationOAuth2ClientsView, OrganisationOAuth2ClientView
from software_statement.views import SoftwareStatementView
from data_disclosure_agreement_record.views import DataDisclosureAgreementRecordView, SignedAgreementsView, SignedAgreementView, DataDisclosureAgreementRecordSignInStatusView
from b2b_connection.views import B2BConnectionsView, B2BConnectionView

urlpatterns = [
    path("/", OrganisationView.as_view(), name="organisation"),
    path("/code-of-conduct", CodeOfConductUpdateView.as_view(), name="update_code_of_conduct"),
    path("/coverimage/",
        OrganisationCoverImageView.as_view(), name="organisation_cover_image"),
    path("/logoimage/",
        OrganisationLogoImageView.as_view(), name="logo_image"),
    path("/identity/",OrganisationIdentityView.as_view(), name="organisation_identity"),
    path("/oauth2-client/", OAuth2ClientView.as_view(), name='create-auth2-client'),
    path("/oauth2-client/<uuid:pk>/", OAuth2ClientView.as_view(), name='client-detail'),
    path("/oauth2-clients/", OAuth2ClientsView.as_view(), name="oauth-clients"),
    path("/software-statement/",SoftwareStatementView.as_view(), name="organisation_software_statement"),
    path("/oauth2-client-external/", OrganisationOAuth2ClientView.as_view(), name='create-auth2-client-external'),
    path("/oauth2-client-external/<uuid:pk>/", OrganisationOAuth2ClientView.as_view(), name='client-detail-external'),
    path("/oauth2-clients-external/", OrganisationOAuth2ClientsView.as_view(), name="oauth-clients-external"),
    path("/data-disclosure-agreement/<str:dataDisclosureAgreementId>/",
          DataDisclosureAgreementRecordView.as_view(), name="sign-with-business-wallet"),
    path("/data-disclosure-agreement/<str:dataDisclosureAgreementId>/status/",
          DataDisclosureAgreementRecordSignInStatusView.as_view(), name="get-sign-with-business-wallet-status"),
    path("/b2b-connection/<uuid:pk>/",B2BConnectionView.as_view(), name="read-b2b-connection"),
    path("/b2b-connections/",B2BConnectionsView.as_view(), name="list-b2b-connections"),
    path("/data-disclosure-agreement-record/<uuid:pk>/",SignedAgreementView.as_view(), name="read-signed-agreement"),
    path("/data-disclosure-agreement-records/",SignedAgreementsView.as_view(), name="list-signed-agreements"),
]