from django.urls import path
from .views import DataDisclosureAgreementView, DataDisclosureAgreementUpdateView, DataDisclosureAgreementTempleteView, DataDisclosureAgreementTemplateUpdateView


urlpatterns = [

     # path("/<uuid:dataDisclosureAgreementId>/",
     #     DataDisclosureAgreementView.as_view(), name="dataDisclosureAgreement"),
     # path("/<uuid:dataDisclosureAgreementId>/status/",
     #     DataDisclosureAgreementUpdateView.as_view(), name="update_data_disclosure_agreement_status"),
     path("/<uuid:dataDisclosureAgreementId>/",
         DataDisclosureAgreementTempleteView.as_view(), name="dataDisclosureAgreement"),
     path("/<uuid:dataDisclosureAgreementId>/status/",
         DataDisclosureAgreementTemplateUpdateView.as_view(), name="update_data_disclosure_agreement_status"),
]
