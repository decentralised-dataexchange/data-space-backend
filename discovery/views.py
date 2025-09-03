from django.shortcuts import render
from rest_framework.views import View
from django.http import JsonResponse, HttpResponse

# Create your views here.

class DataMarketPlaceConfigurationView(View):

    def get(self, request):

        scheme = request.scheme
        host = request.get_host()
        base_url = f"{scheme}://{host}"
        authorization_server = f"{base_url}/service"
        notification_endpoint = f"{base_url}/service/notification"
        configuration = {
            "authorization_servers": [authorization_server],
            "notification_endpoint": notification_endpoint
        }

        return JsonResponse(configuration)
    
class DataMarketPlaceAuthorizationConfigurationView(View):

    def get(self, request):

        scheme = request.scheme
        host = request.get_host()
        base_url = f"{scheme}://{host}"
        issuer = f"{base_url}/service"
        token_endpoint = f"{base_url}/service/token"
        configuration = {
            "issuer": issuer,
            "token_endpoint": token_endpoint
        }

        return JsonResponse(configuration)