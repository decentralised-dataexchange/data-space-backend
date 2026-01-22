"""
Webhook module for the Data Marketplace.

This module handles incoming webhook callbacks from external verifiable
credential systems (e.g., ACA-Py, Aries agents). These webhooks notify the
marketplace of credential verification status changes, connection state
updates, and data disclosure agreement events.

The webhooks are typically triggered by:
- Verifiable credential presentation verification results
- DIDComm connection state changes
- Credential issuance status updates
"""

import json

from django.http import HttpRequest, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from rest_framework import status

from config.models import Verification
from connection.models import Connection
from data_disclosure_agreement.models import DataDisclosureAgreement
from organisation.models import OrganisationIdentity
from software_statement.models import SoftwareStatement


@csrf_exempt
@require_POST
def verify_certificate(request: HttpRequest) -> HttpResponse:
    """
    Webhook endpoint for receiving data source verification results.

    Business Context:
        This endpoint receives webhook callbacks when a verifiable presentation
        verification is completed for a data source. Data sources must prove
        their identity through verifiable credentials before they can participate
        in the marketplace.

    Authentication:
        No authentication required. This is a webhook endpoint called by
        trusted infrastructure (verifiable credential agents).
        CSRF is disabled for webhook compatibility.

    Request Format:
        Content-Type: application/json
        {
            "data": {
                "presentation": {
                    "presentationExchangeId": "string",
                    "status": "string",
                    ...additional presentation data...
                }
            }
        }

    Business Logic:
        1. Extracts the presentation exchange ID from the webhook payload
        2. Looks up the corresponding Verification record
        3. Updates the verification state if not already verified
        4. Stores the full presentation record for audit purposes

    Business Rules:
        - Verification state is only updated if current state is not "verified"
        - This prevents re-verification from overwriting confirmed verifications
        - Missing presentationExchangeId results in silent 200 OK response

    Returns:
        HTTP 200 OK in all cases (webhook acknowledgement pattern)
    """
    response = request.body
    response = json.loads(response)
    presentation_exchange_id = response["data"]["presentation"][
        "presentationExchangeId"
    ]
    if not presentation_exchange_id:
        return HttpResponse(status=status.HTTP_200_OK)

    presentation_state = response["data"]["presentation"]["status"]
    presentation_record = response["data"]["presentation"]
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
def verify_ows_certificate(request: HttpRequest) -> HttpResponse:
    """
    Webhook endpoint for receiving organisation identity (OWS) verification results.

    Business Context:
        This endpoint receives webhook callbacks when an Organisation Web Services
        (OWS) certificate verification is completed. OWS certificates prove that
        an organisation is a legitimate participant in the data space ecosystem.

        Unlike data source verification, OWS verification specifically validates
        the organisation's identity and credentials for operating web services.

    Authentication:
        No authentication required. This is a webhook endpoint called by
        trusted infrastructure (verifiable credential agents).
        CSRF is disabled for webhook compatibility.

    Request Format:
        Content-Type: application/json
        {
            "data": {
                "presentation": {
                    "presentationExchangeId": "string",
                    "status": "string",
                    "verified": boolean,
                    ...additional presentation data...
                }
            }
        }

    Business Logic:
        1. Extracts the presentation exchange ID and verification status
        2. Looks up the corresponding OrganisationIdentity record
        3. Updates the verification state if not already verified
        4. Sets isPresentationVerified flag based on verification result

    Business Rules:
        - Verification state is only updated if isPresentationVerified is False
        - This prevents re-verification from modifying confirmed verifications
        - The verified flag from the presentation determines final verification status
        - Missing presentationExchangeId results in silent 200 OK response

    Returns:
        HTTP 200 OK in all cases (webhook acknowledgement pattern)
    """
    response = request.body
    response = json.loads(response)
    presentation_exchange_id = response["data"]["presentation"][
        "presentationExchangeId"
    ]
    if not presentation_exchange_id:
        return HttpResponse(status=status.HTTP_200_OK)

    presentation_state = response["data"]["presentation"]["status"]
    presentation_record = response["data"]["presentation"]
    is_presentation_verified = response["data"]["presentation"]["verified"]
    try:
        identity = OrganisationIdentity.objects.get(
            presentationExchangeId=presentation_exchange_id
        )
    except OrganisationIdentity.DoesNotExist:
        identity = None

    if identity:
        if not identity.isPresentationVerified:
            identity.presentationState = presentation_state
            identity.presentationRecord = presentation_record
            identity.isPresentationVerified = is_presentation_verified
            identity.save()

    return HttpResponse(status=status.HTTP_200_OK)


@csrf_exempt
@require_POST
def receive_ows_issuance_history(request: HttpRequest) -> HttpResponse:
    """
    Webhook endpoint for receiving software statement credential issuance updates.

    Business Context:
        Software statements are verifiable credentials that attest to an
        organisation's software or service configuration. This endpoint
        receives updates about the issuance status of these credentials,
        tracking the lifecycle from issuance request to completion.

        Software statements are used in the OAuth 2.0 Dynamic Client Registration
        context, providing cryptographic proof of client software identity.

    Authentication:
        No authentication required. This is a webhook endpoint called by
        trusted infrastructure (verifiable credential agents).
        CSRF is disabled for webhook compatibility.

    Request Format:
        Content-Type: application/json
        {
            "data": {
                "credential": {
                    "CredentialExchangeId": "string",
                    "status": "string",
                    ...additional credential data...
                }
            }
        }

    Business Logic:
        1. Extracts the credential exchange ID from the webhook payload
        2. Looks up the corresponding SoftwareStatement record
        3. Updates the issuance status and stores the full credential history
        4. History includes all status transitions for audit purposes

    Business Rules:
        - Status is always updated (no idempotency check)
        - Full credential history is stored for compliance and debugging
        - Missing credentialExchangeId results in silent 200 OK response

    Returns:
        HTTP 200 OK in all cases (webhook acknowledgement pattern)
    """
    response = request.body
    response = json.loads(response)
    credential_exchange_id = response["data"]["credential"]["CredentialExchangeId"]
    if not credential_exchange_id:
        return HttpResponse(status=status.HTTP_200_OK)

    issuance_history_status = response["data"]["credential"]["status"]
    issuance_history = response["data"]["credential"]
    try:
        software_statement = SoftwareStatement.objects.get(
            credentialExchangeId=credential_exchange_id
        )
    except SoftwareStatement.DoesNotExist:
        software_statement = None

    if software_statement:
        software_statement.status = issuance_history_status
        software_statement.credentialHistory = issuance_history
        software_statement.save()

    return HttpResponse(status=status.HTTP_200_OK)


@csrf_exempt
@require_POST
def receive_invitation(request: HttpRequest) -> HttpResponse:
    """
    Webhook endpoint for receiving DIDComm connection state updates.

    Business Context:
        This endpoint receives webhook callbacks when a DIDComm connection
        state changes. DIDComm connections are peer-to-peer encrypted
        communication channels established between data marketplace participants.

        These connections are prerequisites for secure data exchange and
        verifiable credential presentation workflows.

    Authentication:
        No authentication required. This is a webhook endpoint called by
        trusted infrastructure (verifiable credential agents).
        CSRF is disabled for webhook compatibility.

    Request Format:
        Content-Type: application/json
        {
            "connection_id": "string",
            "state": "string (invitation|request|response|active|etc.)",
            ...additional connection data...
        }

    Business Logic:
        1. Extracts connection ID and state from the webhook payload
        2. Looks up the corresponding Connection record
        3. When connection becomes "active":
           a. Deletes any existing active connections for the same data source
           b. Updates the connection state to active
        4. This ensures only one active connection per data source

    Business Rules:
        - Only "active" state transitions are processed
        - A data source can only have one active connection at a time
        - Previous active connections are deleted when a new one becomes active
        - This prevents duplicate connections from causing issues
        - Connection record stores the full DIDComm connection data

    Returns:
        HTTP 200 OK in all cases (webhook acknowledgement pattern)
    """
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
                dataSourceId=connection.dataSourceId, connectionState="active"
            ).delete()
            # Update status of the incoming connection
            connection.connectionState = connection_state
            connection.connectionRecord = connection_data
            connection.save()

    return HttpResponse(status=status.HTTP_200_OK)


@csrf_exempt
@require_POST
def receive_data_disclosure_agreement(request: HttpRequest) -> HttpResponse:
    """
    Webhook endpoint for receiving new Data Disclosure Agreement templates.

    Business Context:
        This endpoint receives webhook callbacks when a new Data Disclosure
        Agreement (DDA) template is received over a DIDComm connection.
        DDAs define the terms and conditions under which data can be shared
        between participants in the data space.

        This webhook is triggered when a data source publishes a new DDA
        template through the verifiable credential agent.

    Authentication:
        No authentication required. This is a webhook endpoint called by
        trusted infrastructure (verifiable credential agents).
        CSRF is disabled for webhook compatibility.

    Request Format:
        Content-Type: application/json
        {
            "connection_id": "string",
            "template_id": "string",
            "connection_url": "string",
            "dda": {
                "language": "string",
                "version": "string",
                "dataController": {...},
                "agreementPeriod": int,
                "dataSharingRestrictions": {...},
                "purpose": "string",
                "purposeDescription": "string",
                "lawfulBasis": "string",
                "personalData": [...],
                "codeOfConduct": "string"
            }
        }

    Business Logic:
        1. Extracts DDA data and connection information from the webhook
        2. Looks up the connection to identify the data source
        3. Constructs a normalized DDA record including connection URL
        4. Marks any existing versions of this template as non-latest
        5. Creates a new DDA record linked to the data source

    Business Rules:
        - DDAs are versioned; multiple versions can exist for the same template
        - Only the newest version has isLatestVersion=True
        - DDAs are linked to data sources via the connection
        - Connection must exist for the DDA to be created
        - DDA includes connection URL for establishing data exchange

    Returns:
        HTTP 200 OK in all cases (webhook acknowledgement pattern)
    """
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
