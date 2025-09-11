from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from organisation.models import Organisation
from data_disclosure_agreement.models import DataDisclosureAgreementTemplate

User = get_user_model()

class DataMarketPlaceNotificationView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        # Validate Authorization header (Bearer <token>)
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        if not auth_header.startswith('Bearer '):
            return Response({
                'error': 'invalid_token',
                'error_description': _('Missing or invalid Authorization header')
            }, status=status.HTTP_401_UNAUTHORIZED)
        token = auth_header.split(' ', 1)[1].strip()
        
        # Authenticate token and get user
        authenticator = JWTAuthentication()
        try:
            validated_token = authenticator.get_validated_token(token)
            user = authenticator.get_user(validated_token)
        except Exception as exc:
            return Response({
                'error': 'invalid_token',
                'error_description': _('Token validation failed')
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        if user is None or not user.is_active:
            return Response({
                'error': 'invalid_client',
                'error_description': _('Invalid client credentials')
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        # Find DataSource for this user
        try:
            data_source = Organisation.objects.get(admin=user)
        except Organisation.DoesNotExist:
            return Response({
                'error': 'not_found',
                'error_description': _('No DataSource associated with this token')
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Validate payload
        payload = request.data if request.content_type == 'application/json' else request.POST.dict()
        event_type = payload.get('type')
        event_action = payload.get('event')
        dda_template = payload.get('dataDisclosureAgreementTemplate')
        dda_record = payload.get('dataDisclosureAgreementRecord')
        
        if event_type not in {'dda_template', 'dda_record'}:
            return Response({
                'error': 'invalid_request',
                'error_description': "'type' must be 'dda_template' or 'dda_record'"
            }, status=status.HTTP_400_BAD_REQUEST)
        if event_action not in {'create', 'update', 'delete'}:
            return Response({
                'error': 'invalid_request',
                'error_description': "'event' must be one of 'create', 'update', 'delete'"
            }, status=status.HTTP_400_BAD_REQUEST)
        if event_type == 'dda_template':
            if not isinstance(dda_template, dict) or not dda_template:
                return Response({
                    'error': 'invalid_request',
                    'error_description': "'dataDisclosureAgreementTemplate' is required and must be a non-empty object"
                }, status=status.HTTP_400_BAD_REQUEST)
            missing = _validate_dda_template_required_fields(event_action, dda_template)
            if missing:
                return Response({
                    'error': 'invalid_request',
                    'error_description': 'Missing required fields',
                    'missing': missing
                }, status=status.HTTP_400_BAD_REQUEST)
        if event_type == 'dda_record':
            if not isinstance(dda_record, dict) or not dda_record:
                return Response({
                    'error': 'invalid_request',
                    'error_description': "'dataDisclosureAgreementRecord' is required and must be a non-empty object"
                }, status=status.HTTP_400_BAD_REQUEST)
        
        if event_type == 'dda_template':
            if event_action == 'create':
                create_data_disclosure_agreement(dda_template, data_source)
            elif event_action == 'update':
                create_data_disclosure_agreement(dda_template, data_source)
            elif event_action == 'delete':
                delete_data_disclosure_agreement(dda_template, data_source)
        
        # TODO: support event_type `DDA-record`
        
        response_data = {
            'status': 'ok'
        }
        return Response(response_data, status=status.HTTP_200_OK)
    

def _validate_dda_template_required_fields(event_action: str, dda_template: dict):
    if event_action in {'create', 'update'}:
        required = [
            '@id', 'version', 'language', 'dataController', 'agreementPeriod',
            'dataSharingRestrictions', 'purpose', 'purposeDescription',
            'lawfulBasis', 'codeOfConduct'
        ]
    else:  # delete
        required = ['@id']
    missing = [key for key in required if key not in dda_template or dda_template.get(key) in (None, '')]
    return missing


def create_data_disclosure_agreement(to_be_created_dda: dict, data_source: Organisation):

    dda_version = to_be_created_dda["version"]
    dda_template_id = to_be_created_dda["@id"]

    # Iterate through existing DDAs and mark `isLatestVersion=false`
    existing_ddas = DataDisclosureAgreementTemplate.objects.filter(
        templateId=dda_template_id, isLatestVersion=True, organisationId=data_source,
    )
    for existing_dda in existing_ddas:
        existing_dda.isLatestVersion = False
        existing_dda.save()

    dda = DataDisclosureAgreementTemplate.objects.create(
        version=dda_version,
        templateId=dda_template_id,
        organisationId=data_source,
        dataDisclosureAgreementRecord=to_be_created_dda,
    )
    dda.save()
    return


def delete_data_disclosure_agreement(to_be_deleted_dda: dict, data_source: Organisation):

    dda_template_id = to_be_deleted_dda["@id"]

    deleted_count, _ = DataDisclosureAgreementTemplate.objects.filter(
        templateId=dda_template_id, organisationId=data_source,
    ).delete()

    return deleted_count
    