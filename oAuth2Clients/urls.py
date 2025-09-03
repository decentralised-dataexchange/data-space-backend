from django.urls import path
from .views import OAuth2ClientView

app_name = 'oauth2clients'

urlpatterns = [
    # List (GET) and Create (POST)
    path('/', OAuth2ClientView.as_view(), name='create-auth2-client'),
    
    # Retrieve, Update, Delete (with pk) - uses OAuth2ClientView
    path('/<uuid:pk>/', OAuth2ClientView.as_view(), name='client-detail'),
]
