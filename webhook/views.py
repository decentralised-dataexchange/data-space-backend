from django.views.decorators.http import require_POST
from django.http import HttpResponse
from config.models import Verification
from connection.models import Connection
from rest_framework import status
from django.views.decorators.csrf import csrf_exempt
import json

# Create your views here.
@csrf_exempt
@require_POST
def verify_certificate(request):
    response = request.body
    response = json.loads(response)
    presentation_exchange_id = response["data"]["presentation"]["presentationExchangeId"]
    presentation_state = response["data"]["presentation"]["state"]
    presentation_record = response["data"]["presentation"]
    try:
        verification = Verification.objects.get(
            presentationExchangeId=presentation_exchange_id)
    except Verification.DoesNotExist:
        verification = None

    if verification:
        if verification.presentationState != "verified":
            verification.presentationState = presentation_state
            verification.presentationRecord = presentation_record
            verification.save()

    return HttpResponse(status=status.HTTP_200_OK)

@csrf_exempt
@require_POST
def receive_invitation(request):
    
    response = request.body
    response = json.loads(response)
    connection_id = response["data"]["connection"]["connectionId"]
    connection_data = response["data"]["connection"]
    connection_data.pop("id", None)

    try:
        connection = Connection.objects.get(
            connectionId=connection_id)
    except Verification.DoesNotExist:
        connection = None
    
    if connection:
        if connection.state != "active":
            for key, value in connection_data.items():
                        setattr(connection, key, value)
                    
            connection.save()

    return HttpResponse(status=status.HTTP_200_OK)


