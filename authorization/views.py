import base64
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from django.contrib.auth import authenticate, get_user_model
from rest_framework_simplejwt.tokens import AccessToken

User = get_user_model()

@method_decorator(csrf_exempt, name='dispatch')
class DataMarketPlaceTokenView(APIView):
    """
    OAuth 2.0 Token endpoint (client_credentials) using Basic auth.
    - Authorization: Basic base64(email:password)
    - Body: grant_type=client_credentials (form or json)
    Returns JWT access token and expiry.
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
            client_id, password = decoded.split(':', 1)
        except Exception:
            return Response({
                'error': 'invalid_client',
                'error_description': 'Invalid Basic Authorization header'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        # Authenticate against DataspaceUser (email/password)
        user = authenticate(request, username=client_id, password=password)
        if user is None or not user.is_active:
            return Response({
                'error': 'invalid_client',
                'error_description': 'Invalid client credentials'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        # Issue JWT access token
        access = AccessToken.for_user(user)
        expires_in = int(access.lifetime.total_seconds())
        
        response_data = {
            'access_token': str(access),
            'token_type': 'Bearer',
            'expires_in': expires_in,
        }
        return Response(response_data, status=status.HTTP_200_OK)