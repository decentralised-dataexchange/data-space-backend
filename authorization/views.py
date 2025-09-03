import base64
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import AccessToken
from oAuth2Clients.models import OAuth2Clients
from organisation.models import Organisation

User = get_user_model()

@method_decorator(csrf_exempt, name='dispatch')
class DataMarketPlaceTokenView(APIView):
    """
    OAuth 2.0 Token endpoint (client_credentials) using Basic auth.
    - Authorization: Basic base64(client_id:client_secret)
    - Body: grant_type=client_credentials (form or json)
    Finds the Organisation via OAuth2Clients and issues a JWT for the organisation admin.
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        # Extract grant_type from form or JSON
        grant_type = None
        if request.content_type == 'application/json':
            grant_type = (request.data or {}).get('grant_type')
        else:
            grant_type = request.POST.get('grant_type')
        if grant_type != 'client_credentials':
            return Response({
                'error': 'unsupported_grant_type',
                'error_description': "Only 'client_credentials' is supported"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Parse Basic auth header
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        if not auth_header.startswith('Basic '):
            return Response({
                'error': 'invalid_client',
                'error_description': 'Missing Basic Authorization header'
            }, status=status.HTTP_401_UNAUTHORIZED)
        try:
            b64 = auth_header.split(' ', 1)[1].strip()
            decoded = base64.b64decode(b64).decode('utf-8')
            if ':' not in decoded:
                raise ValueError('Invalid basic auth format')
            client_id, client_secret = decoded.split(':', 1)
        except Exception:
            return Response({
                'error': 'invalid_client',
                'error_description': 'Invalid Basic Authorization header'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        # Find OAuth2 client and associated organisation
        try:
            oauth_client = OAuth2Clients.objects.select_related('organisation').get(
                client_id=client_id,
                client_secret=client_secret,
                is_active=True
            )
        except OAuth2Clients.DoesNotExist:
            return Response({
                'error': 'invalid_client',
                'error_description': 'Invalid client credentials'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        organisation = oauth_client.organisation
        try:
            admin_user = organisation.admin
        except Exception:
            return Response({
                'error': 'server_error',
                'error_description': 'Organisation admin not found for this client'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        if not admin_user or not admin_user.is_active:
            return Response({
                'error': 'invalid_client',
                'error_description': 'Organisation admin is inactive or missing'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        # Issue JWT access token for organisation admin
        access = AccessToken.for_user(admin_user)
        expires_in = int(access.lifetime.total_seconds())
        
        response_data = {
            'access_token': str(access),
            'token_type': 'Bearer',
            'expires_in': expires_in,
        }
        return Response(response_data, status=status.HTTP_200_OK)