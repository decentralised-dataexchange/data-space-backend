from django.urls import path

from . import views

urlpatterns = [
    path("topic/connections/", views.receive_invitation),
    path("topic/present_proof/", views.verify_certificate),
    path(
        "topic/published_data_disclosure_agreement/",
        views.receive_data_disclosure_agreement,
    ),
    path("topic/ows/present_proof/", views.verify_ows_certificate),
    path("topic/ows/issue_credential/", views.receive_ows_issuance_history),
]
