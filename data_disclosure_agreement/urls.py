from django.urls import path
from .views import DataDisclosureAgreementView, DataDisclosureAgreementUpdateView, DataDisclosureAgreementTempleteView, DataDisclosureAgreementTemplateUpdateView, DataDisclosureAgreementHistoryView


urlpatterns = [

     # path("/<uuid:dataDisclosureAgreementId>/",
     #     DataDisclosureAgreementView.as_view(), name="dataDisclosureAgreement"),
     # path("/<uuid:dataDisclosureAgreementId>/status/",
     #     DataDisclosureAgreementUpdateView.as_view(), name="update_data_disclosure_agreement_status"),
     path("/<str:dataDisclosureAgreementId>/",
         DataDisclosureAgreementTempleteView.as_view(), name="dataDisclosureAgreement"),
     path("/<str:dataDisclosureAgreementId>/status/",
         DataDisclosureAgreementTemplateUpdateView.as_view(), name="update_data_disclosure_agreement_status"),
    path("/<str:dataDisclosureAgreementId>/history/",
         DataDisclosureAgreementHistoryView.as_view(), name="list_data_disclosure_agreement_history"),
]
