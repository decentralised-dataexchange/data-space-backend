from django.urls import path

from . import views

urlpatterns = [
    path('topic/present_proof/', views.verify_certificate),
]
