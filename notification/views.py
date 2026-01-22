"""
Notification module for the Data Marketplace.

This module implements the notification endpoint that receives asynchronous
events from the Data Intermediary Service Provider (DISP). It handles
synchronization of Data Disclosure Agreement (DDA) templates, DDA records,
and B2B connections between the DISP and the local data marketplace instance.
"""

import json
from typing import Any

from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication

from b2b_connection.models import B2BConnection
from data_disclosure_agreement.models import DataDisclosureAgreementTemplate
from data_disclosure_agreement_record.models import (
    DataDisclosureAgreementRecord,
    DataDisclosureAgreementRecordHistory,
)
from organisation.models import Organisation

User = get_user_model()


class DataMarketPlaceNotificationView(APIView):
    """
    Notification endpoint for receiving events from the Data Intermediary Service Provider.

    This endpoint receives webhook-style notifications from the DISP when significant
    events occur, such as creation, update, or deletion of DDA templates, DDA records,
    or B2B connections. It synchronizes the local data marketplace state with the DISP.

    Business Context:
        In the data space architecture, the DISP acts as a central coordinator for
        data exchange agreements. This notification endpoint allows the DISP to push
        updates to registered data sources, ensuring consistency across the ecosystem.

        Key entities synchronized:
        - DDA Templates: Define the terms and conditions for data sharing
        - DDA Records: Capture the actual agreements signed between parties
        - B2B Connections: Represent relationships between organisations

    Authentication:
        Requires a valid JWT Bearer token in the Authorization header.
        The token must belong to an active user who is an organisation admin.
        Note: permission_classes is AllowAny, but manual JWT validation is performed.

    Request Format:
        Content-Type: application/json
        {
            "type": "dda_template" | "dda_record" | "b2b_connection",
            "event": "create" | "update" | "delete",
            "dataDisclosureAgreementTemplate": {...},  // for dda_template type
            "dataDisclosureAgreementRecord": {...},    // for dda_record type
            "b2bConnection": {...}                     // for b2b_connection type
        }

    Response Format (200 OK):
        {"status": "ok"}

    Business Rules:
        - Token must be valid and belong to an active organisation admin
        - Event type must be one of: dda_template, dda_record, b2b_connection
        - Event action must be one of: create, update, delete
        - Required payload object must be present based on event type

    Errors:
        - 400: Invalid request format or missing required fields
        - 401: Invalid or missing authentication token
        - 404: No organisation associated with the token
    """

    permission_classes = [AllowAny]

    def post(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """
        Process incoming notification events from the DISP.

        Business Logic:
            1. Validates the JWT Bearer token from the Authorization header
            2. Identifies the organisation (data source) associated with the token
            3. Validates the notification payload structure
            4. Routes the event to the appropriate handler based on type:
               - dda_template: Creates/updates/deletes DDA templates
               - dda_record: Creates/updates DDA agreement records
               - b2b_connection: Creates/updates/deletes B2B connections

        Event Processing:
            - DDA Template Create/Update: Marks existing versions as non-latest,
              creates new template version
            - DDA Template Delete: Archives existing templates (soft delete)
            - DDA Record Create/Update: Links to template or creates orphan record
            - B2B Connection Create/Update: Upserts connection record
            - B2B Connection Delete: Hard deletes connection record

        Returns:
            Response with {"status": "ok"} on success.
            Error response with error and error_description on failure.
        """
        # Validate Authorization header (Bearer <token>)
        auth_header = request.META.get("HTTP_AUTHORIZATION", "")
        if not auth_header.startswith("Bearer "):
            return Response(
                {
                    "error": "invalid_token",
                    "error_description": _("Missing or invalid Authorization header"),
                },
                status=status.HTTP_401_UNAUTHORIZED,
            )
        token = auth_header.split(" ", 1)[1].strip()

        # Authenticate token and get user
        authenticator = JWTAuthentication()
        try:
            validated_token = authenticator.get_validated_token(token)
            user = authenticator.get_user(validated_token)
        except Exception:
            return Response(
                {
                    "error": "invalid_token",
                    "error_description": _("Token validation failed"),
                },
                status=status.HTTP_401_UNAUTHORIZED,
            )

        if user is None or not user.is_active:
            return Response(
                {
                    "error": "invalid_client",
                    "error_description": _("Invalid client credentials"),
                },
                status=status.HTTP_401_UNAUTHORIZED,
            )

        # Find DataSource for this user
        try:
            data_source = Organisation.objects.get(admin=user)
        except Organisation.DoesNotExist:
            return Response(
                {
                    "error": "not_found",
                    "error_description": _("No DataSource associated with this token"),
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        # Validate payload
        payload = (
            request.data
            if request.content_type == "application/json"
            else request.POST.dict()
        )
        event_type = payload.get("type")
        event_action = payload.get("event")
        dda_template_revision = payload.get("dataDisclosureAgreementTemplate")
        dda_record = payload.get("dataDisclosureAgreementRecord")
        b2b_connection = payload.get("b2bConnection")

        if event_type not in {"dda_template", "dda_record", "b2b_connection"}:
            return Response(
                {
                    "error": "invalid_request",
                    "error_description": "'type' must be 'dda_template_revision' or 'dda_record'",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        if event_action not in {"create", "update", "delete"}:
            return Response(
                {
                    "error": "invalid_request",
                    "error_description": "'event' must be one of 'create', 'update', 'delete'",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        if event_type == "dda_template":
            if not isinstance(dda_template_revision, dict) or not dda_template_revision:
                return Response(
                    {
                        "error": "invalid_request",
                        "error_description": "'dataDisclosureAgreementTemplate' is required and must be a non-empty object",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
            serialized_snapshot = json.loads(
                dda_template_revision["serializedSnapshot"]
            )
            dda_template = json.loads(serialized_snapshot["objectData"])
            missing = _validate_dda_template_required_fields(event_action, dda_template)
            if missing:
                return Response(
                    {
                        "error": "invalid_request",
                        "error_description": "Missing required fields",
                        "missing": missing,
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
        if event_type == "dda_record":
            if not isinstance(dda_record, dict) or not dda_record:
                return Response(
                    {
                        "error": "invalid_request",
                        "error_description": "'dataDisclosureAgreementRecord' is required and must be a non-empty object",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
        if event_type == "b2b_connection":
            if not isinstance(b2b_connection, dict) or not b2b_connection:
                return Response(
                    {
                        "error": "invalid_request",
                        "error_description": "'b2bConnection' is required and must be a non-empty object",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

        if event_type == "dda_template":
            # dda_template_revision is validated above as a dict
            revision_dict = (
                dda_template_revision if isinstance(dda_template_revision, dict) else {}
            )
            if event_action == "create":
                create_data_disclosure_agreement(
                    to_be_created_dda=dda_template,
                    revision=revision_dict,
                    data_source=data_source,
                )
            elif event_action == "update":
                create_data_disclosure_agreement(
                    to_be_created_dda=dda_template,
                    revision=revision_dict,
                    data_source=data_source,
                )
            elif event_action == "delete":
                delete_data_disclosure_agreement(
                    to_be_deleted_dda=dda_template,
                    revision=revision_dict,
                    data_source=data_source,
                )
        elif event_type == "dda_record":
            # dda_record is validated above as a dict
            record_dict = dda_record if isinstance(dda_record, dict) else {}
            if event_action == "create":
                create_data_disclosure_agreement_record(
                    dda_record=record_dict, organisation=data_source
                )
            if event_action == "update":
                create_data_disclosure_agreement_record(
                    dda_record=record_dict, organisation=data_source
                )
        elif event_type == "b2b_connection":
            # b2b_connection is validated above as a dict
            connection_dict = b2b_connection if isinstance(b2b_connection, dict) else {}
            if event_action == "create":
                create_b2b_connection(
                    b2b_connection=connection_dict, organisation=data_source
                )
            elif event_action == "update":
                create_b2b_connection(
                    b2b_connection=connection_dict, organisation=data_source
                )
            elif event_action == "delete":
                delete_b2b_connection(
                    b2b_connection=connection_dict, organisation=data_source
                )
            else:
                pass

        else:
            return Response(
                {
                    "error": "invalid_request",
                    "error_description": "Event type is not supported",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # TODO: support event_type `DDA-record`

        response_data = {"status": "ok"}
        return Response(response_data, status=status.HTTP_200_OK)


def _validate_dda_template_required_fields(
    event_action: str, dda_template: dict[str, Any]
) -> list[str]:
    """
    Validate that the DDA template contains all required fields for the given action.

    Business Logic:
        For create/update actions, validates that all required DDA template
        fields are present and non-empty. For delete actions, only the @id
        is required to identify the template to remove.

    Args:
        event_action: The action being performed ("create", "update", or "delete")
        dda_template: The DDA template data to validate

    Returns:
        List of missing field names. Empty list if validation passes.

    Required Fields (create/update):
        - @id: Unique identifier for the DDA template
        - version: Version number of the template
        - language: Language code for the agreement text
        - dataController: Information about the data controller
        - agreementPeriod: Duration of the agreement
        - dataSharingRestrictions: Constraints on data sharing
        - purpose: Purpose of data collection/sharing
        - purposeDescription: Detailed description of purpose
        - lawfulBasis: Legal basis for data processing
        - codeOfConduct: Reference to applicable code of conduct
    """
    if event_action in {"create", "update"}:
        required = [
            "@id",
            "version",
            "language",
            "dataController",
            "agreementPeriod",
            "dataSharingRestrictions",
            "purpose",
            "purposeDescription",
            "lawfulBasis",
            "codeOfConduct",
        ]
    else:  # delete
        required = ["@id"]
    missing = [
        key
        for key in required
        if key not in dda_template or dda_template.get(key) in (None, "")
    ]
    return missing


def create_data_disclosure_agreement(
    to_be_created_dda: dict[str, Any],
    revision: dict[str, Any],
    data_source: Organisation,
) -> None:
    """
    Create or update a Data Disclosure Agreement template.

    Business Logic:
        Creates a new version of a DDA template in the local database.
        When a new version is created, all existing versions with the same
        templateId are marked as non-latest (isLatestVersion=False) to
        maintain version history while clearly indicating the current version.

    Args:
        to_be_created_dda: The DDA template data including @id, version, etc.
        revision: The revision metadata from the DISP including serialized snapshot
        data_source: The organisation (data source) that owns this DDA template

    Business Rules:
        - Multiple versions of the same template can exist (identified by @id)
        - Only the most recently created version has isLatestVersion=True
        - All DDA data is stored including the full revision history

    Side Effects:
        - Updates isLatestVersion to False for all existing versions
        - Creates a new DataDisclosureAgreementTemplate record
    """
    dda_version = to_be_created_dda["version"]
    dda_template_id = to_be_created_dda["@id"]

    # Iterate through existing DDAs and mark `isLatestVersion=false`
    existing_ddas = DataDisclosureAgreementTemplate.objects.filter(
        templateId=dda_template_id,
        organisationId=data_source,
    )
    for existing_dda in existing_ddas:
        existing_dda.isLatestVersion = False
        existing_dda.save()

    dda = DataDisclosureAgreementTemplate.objects.create(
        version=dda_version,
        templateId=dda_template_id,
        organisationId=data_source,
        dataDisclosureAgreementRecord=to_be_created_dda,
        dataDisclosureAgreementTemplateRevision=revision,
        dataDisclosureAgreementTemplateRevisionId=revision.get("id"),
    )
    dda.save()
    return


def delete_data_disclosure_agreement(
    to_be_deleted_dda: dict[str, Any],
    revision: dict[str, Any],
    data_source: Organisation,
) -> int:
    """
    Archive a Data Disclosure Agreement template (soft delete).

    Business Logic:
        Instead of hard-deleting DDA templates, this function performs a
        soft delete by setting the status to "archived". This preserves
        the DDA template for historical records and audit purposes.

    Args:
        to_be_deleted_dda: The DDA template data containing at least the @id
        revision: The revision metadata (currently unused, reserved for future use)
        data_source: The organisation (data source) that owns this DDA template

    Returns:
        The number of DDA template records that were archived.

    Business Rules:
        - All versions of the template are archived (matching by templateId)
        - Only templates belonging to the specified organisation are affected
        - Archives preserve all original data for compliance purposes

    Note:
        FIXME: DISP is sending revision upon delete, need to handle it.
    """
    dda_template_id = to_be_deleted_dda["@id"]

    updated_count = DataDisclosureAgreementTemplate.objects.filter(
        templateId=dda_template_id,
        organisationId=data_source,
    ).update(status="archived")

    return updated_count


def create_data_disclosure_agreement_record(
    dda_record: dict[str, Any], organisation: Organisation
) -> None:
    """
    Create or update a Data Disclosure Agreement record (signed agreement).

    Business Logic:
        DDA records represent actual signed agreements between parties,
        as opposed to DDA templates which are the unsigned agreement definitions.
        This function handles both the initial creation and subsequent updates
        of agreement records.

        The function determines signature status by checking if both data source
        and data using service have provided signatures. The agreement state is
        set to "signed" only when both parties have signed.

    Args:
        dda_record: The DDA record data including signatures, template reference, etc.
        organisation: The organisation associated with this DDA record

    Record Storage Strategy:
        - If a matching DDA template exists: Creates a DataDisclosureAgreementRecordHistory
          entry linked to the template for full traceability
        - If no matching template exists: Creates a DataDisclosureAgreementRecord
          as an orphan record (may happen during sync issues)

    Business Rules:
        - Records are linked to templates via templateRevisionId and templateId
        - State is "signed" only when both parties have provided signatures
        - optIn status tracks consent for ongoing data sharing
        - Missing template reference fields cause silent skip (no record created)
    """
    dda_record_id = dda_record.get("canonicalId")
    dda_template_revision_id = dda_record.get(
        "dataDisclosureAgreementTemplateRevision", {}
    ).get("id")
    dda_template_id = dda_record.get("dataDisclosureAgreementTemplateRevision", {}).get(
        "objectId"
    )
    is_data_source_signed = (
        True
        if dda_record.get("dataSourceSignature", {}).get("signature", None)
        else False
    )
    is_data_using_service_signed = (
        True
        if dda_record.get("dataUsingServiceSignature", {}).get("signature", None)
        else False
    )
    state = (
        "signed"
        if is_data_source_signed and is_data_using_service_signed
        else "unsigned"
    )
    opt_in = dda_record.get("optIn")

    try:
        existing_dda = DataDisclosureAgreementTemplate.objects.filter(
            templateId=dda_template_id,
            organisationId=organisation,
            dataDisclosureAgreementTemplateRevisionId=dda_template_revision_id,
        ).first()
    except DataDisclosureAgreementTemplate.DoesNotExist:
        existing_dda = None

    if not dda_template_revision_id or not dda_template_id:
        return

    if existing_dda:
        DataDisclosureAgreementRecordHistory.objects.create(
            organisationId=organisation,
            dataDisclosureAgreementRecord=dda_record,
            dataDisclosureAgreementTemplate=existing_dda,
            dataDisclosureAgreementTemplateId=existing_dda.templateId,
            dataDisclosureAgreementTemplateRevisionId=dda_template_revision_id,
            dataDisclosureAgreementRecordId=dda_record_id,
            optIn=opt_in,
            state=state,
        ).save()
    else:
        DataDisclosureAgreementRecord.objects.create(
            organisationId=organisation,
            dataDisclosureAgreementRecord=dda_record,
            dataDisclosureAgreementTemplateId=dda_template_id,
            dataDisclosureAgreementTemplateRevisionId=dda_template_revision_id,
            dataDisclosureAgreementRecordId=dda_record_id,
            optIn=opt_in,
            state=state,
        ).save()
        return


def create_b2b_connection(
    b2b_connection: dict[str, Any], organisation: Organisation
) -> None:
    """
    Create or update a B2B (Business-to-Business) connection record.

    Business Logic:
        B2B connections represent established relationships between organisations
        in the data space ecosystem. These connections enable data sharing
        workflows between the connected parties.

        This function implements upsert logic: if a connection with the same ID
        already exists, it updates the record; otherwise, it creates a new one.

    Args:
        b2b_connection: The B2B connection data from the DISP
        organisation: The organisation that owns this connection

    Business Rules:
        - Each B2B connection is uniquely identified by its ID within an organisation
        - Connections store the full connection record as received from the DISP
        - Updates replace the entire connection record (not partial updates)
    """
    b2b_connection_id = b2b_connection.get("id")

    try:
        existing_b2b_connection = B2BConnection.objects.filter(
            b2bConnectionId=b2b_connection_id,
            organisationId=organisation,
        ).first()
    except B2BConnection.DoesNotExist:
        existing_b2b_connection = None

    if existing_b2b_connection:
        existing_b2b_connection.b2bConnectionRecord = b2b_connection
        existing_b2b_connection.save()
    else:
        B2BConnection.objects.create(
            organisationId=organisation,
            b2bConnectionRecord=b2b_connection,
            b2bConnectionId=b2b_connection_id,
        ).save()
    return


def delete_b2b_connection(
    b2b_connection: dict[str, Any], organisation: Organisation
) -> None:
    """
    Delete a B2B (Business-to-Business) connection record.

    Business Logic:
        Performs a hard delete of the B2B connection when the relationship
        between organisations is terminated. Unlike DDA templates which are
        archived, B2B connections are permanently removed as they don't
        contain agreement data that needs to be retained for compliance.

    Args:
        b2b_connection: The B2B connection data containing at least the id
        organisation: The organisation that owns this connection

    Business Rules:
        - Connection must belong to the specified organisation
        - Deletion is permanent (hard delete)
        - Non-existent connections are silently ignored (idempotent)
    """
    b2b_connection_id = b2b_connection.get("id")

    try:
        existing_b2b_connection = B2BConnection.objects.get(
            b2bConnectionId=b2b_connection_id,
            organisationId=organisation,
        )
        existing_b2b_connection.delete()
    except B2BConnection.DoesNotExist:
        existing_b2b_connection = None

    return
