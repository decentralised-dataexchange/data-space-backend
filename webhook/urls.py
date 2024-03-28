from django.urls import path

from . import views

urlpatterns = [
    path('topic/connections/',views.receive_invitation),
    path('topic/present_proof/', views.verify_certificate),
]
