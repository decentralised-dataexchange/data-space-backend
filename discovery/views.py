from typing import Any

from constance import config
from django.http import HttpRequest, JsonResponse
from django.views import View

# Create your views here.


class DataMarketPlaceConfigurationView(View):
    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> JsonResponse:
        base_url = config.BASE_URL
        data_space_endpoint = f"{base_url}/service"
        authorization_server = f"{base_url}/service"
        notification_endpoint = f"{base_url}/service/notification"
        configuration = {
            "data_space_endpoint": data_space_endpoint,
            "authorization_servers": [authorization_server],
            "notification_endpoint": notification_endpoint,
        }

        return JsonResponse(configuration)


class DataMarketPlaceAuthorizationConfigurationView(View):
    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> JsonResponse:
        base_url = config.BASE_URL
        issuer = f"{base_url}/service"
        token_endpoint = f"{base_url}/service/token"
        configuration = {"issuer": issuer, "token_endpoint": token_endpoint}

        return JsonResponse(configuration)
