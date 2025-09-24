from django.shortcuts import render
from rest_framework.views import View
from django.http import JsonResponse, HttpResponse
from constance import config

# Create your views here.

class DataMarketPlaceConfigurationView(View):

    def get(self, request):
        base_url = config.BASE_URL
        data_space_endpoint = f"{base_url}/service"
        authorization_server = f"{base_url}/service"
        notification_endpoint = f"{base_url}/service/notification"
        configuration = {
            "data_space_endpoint": data_space_endpoint,
            "authorization_servers": [authorization_server],
            "notification_endpoint": notification_endpoint
        }

        return JsonResponse(configuration)
    
class DataMarketPlaceAuthorizationConfigurationView(View):

    def get(self, request):

        base_url = config.BASE_URL
        issuer = f"{base_url}/service"
        token_endpoint = f"{base_url}/service/token"
        configuration = {
            "issuer": issuer,
            "token_endpoint": token_endpoint
        }

        return JsonResponse(configuration)