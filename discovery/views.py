from django.shortcuts import render
from rest_framework.views import View
from django.http import JsonResponse, HttpResponse
from dataspace_backend.settings import (
    BASE_URL,
)

# Create your views here.

class DataMarketPlaceConfigurationView(View):

    def get(self, request):

        data_space_endpoint = f"{BASE_URL}/service"
        authorization_server = f"{BASE_URL}/service"
        notification_endpoint = f"{BASE_URL}/service/notification"
        configuration = {
            "data_space_endpoint": data_space_endpoint,
            "authorization_servers": [authorization_server],
            "notification_endpoint": notification_endpoint
        }

        return JsonResponse(configuration)
    
class DataMarketPlaceAuthorizationConfigurationView(View):

    def get(self, request):

        issuer = f"{BASE_URL}/service"
        token_endpoint = f"{BASE_URL}/service/token"
        configuration = {
            "issuer": issuer,
            "token_endpoint": token_endpoint
        }

        return JsonResponse(configuration)