from django.views.decorators.http import require_POST
from django.http import HttpResponse
from config.models import Verification
from connection.models import Connection
from rest_framework import status
from django.views.decorators.csrf import csrf_exempt
import json
from data_disclosure_agreement.models import DataDisclosureAgreement
from django.db.models.signals import post_save
from data_disclosure_agreement.signals import (
    query_ddas_and_update_is_latest_flag_to_false_for_previous_versions,
)


# Create your views here.
@csrf_exempt
@require_POST
def verify_certificate(request):
    response = request.body
    response = json.loads(response)
    presentation_exchange_id = response["presentation_exchange_id"]
    presentation_state = response["state"]
    presentation_record = response
    try:
        verification = Verification.objects.get(
            presentationExchangeId=presentation_exchange_id
        )
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
    connection_id = response["connection_id"]
    connection_state = response["state"]
    connection_data = response

    try:
        connection = Connection.objects.get(connectionId=connection_id)
    except Connection.DoesNotExist:
        connection = None

    if connection:
        if connection_state == "active" and connection.connectionState != "active":
            # Delete existing connections with active status for this particular data source
            Connection.objects.filter(
                dataSourceId=connection.dataSourceId,
                connectionState="active"
            ).delete()
            # Update status of the incoming connection
            connection.connectionState = connection_state
            connection.connectionRecord = connection_data
            connection.save()

    return HttpResponse(status=status.HTTP_200_OK)


@csrf_exempt
@require_POST
def receive_data_disclosure_agreement(request):

    response = request.body
    response = json.loads(response)
    connection_id = response["connection_id"]
    dda_version = response["dda"]["version"]
    dda_template_id = response["template_id"]

    dda_connection = {"invitationUrl": response["connection_url"]}

    try:
        connection = Connection.objects.get(connectionId=connection_id)
    except Connection.DoesNotExist:
        connection = None

    if connection:
        data_disclosure_agreement = {
            "language": response["dda"]["language"],
            "version": response["dda"]["version"],
            "templateId": dda_template_id,
            "dataController": response["dda"]["dataController"],
            "agreementPeriod": response["dda"]["agreementPeriod"],
            "dataSharingRestrictions": response["dda"]["dataSharingRestrictions"],
            "purpose": response["dda"]["purpose"],
            "purposeDescription": response["dda"]["purposeDescription"],
            "lawfulBasis": response["dda"]["lawfulBasis"],
            "personalData": response["dda"]["personalData"],
            "codeOfConduct": response["dda"]["codeOfConduct"],
            "connection": dda_connection,
        }

        # Iterate through existing DDAs and mark `isLatestVersion=false`
        existing_ddas = DataDisclosureAgreement.objects.filter(
            templateId=dda_template_id, isLatestVersion=True
        )
        for existing_dda in existing_ddas:
            existing_dda.isLatestVersion = False
            existing_dda.save()


        dda = DataDisclosureAgreement.objects.create(
            version=dda_version,
            templateId=dda_template_id,
            dataSourceId=connection.dataSourceId,
            dataDisclosureAgreementRecord=data_disclosure_agreement,
        )
        dda.save()

    return HttpResponse(status=status.HTTP_200_OK)
