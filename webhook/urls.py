from django.urls import path

from . import views

urlpatterns = [
    path('topic/connections/',views.receive_invitation),
    path('topic/present_proof/', views.verify_certificate),
    path('topic/published_data_disclosure_agreement/',views.receive_data_disclosure_agreement),
]
