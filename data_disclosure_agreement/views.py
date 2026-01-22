"""
Data Disclosure Agreement Views Module

This module provides API endpoints for managing Data Disclosure Agreements (DDAs).
DDAs are legal contracts that define how personal data can be shared between
Data Sources and Data Using Services within the data space ecosystem.

Business Context:
- DDAs establish the legal basis for data sharing between organizations
- They contain terms, conditions, and purposes for data processing
- DDAs go through a lifecycle: unlisted -> awaitingForApproval -> approved -> listed
- Templates are used by Data Source organisations to define agreement terms
- Versioning is supported for audit trails and compliance

Key Concepts:
- DataDisclosureAgreement: Published DDA associated with a Data Source
- DataDisclosureAgreementTemplate: Editable DDA template owned by an Organisation
- Status workflow: unlisted <-> awaitingForApproval -> approved -> listed -> unlisted
"""

from typing import Any

from django.http import JsonResponse
from rest_framework import permissions, status
from rest_framework.request import Request
from rest_framework.views import APIView

from data_disclosure_agreement_record.models import DataDisclosureAgreementRecordHistory
from data_disclosure_agreement_record.serializers import (
    DataDisclosureAgreementRecordHistorySerializer,
)
from dataspace_backend.utils import (
    get_datasource_or_400,
    get_organisation_or_400,
    paginate_queryset,
)

from .models import DataDisclosureAgreement, DataDisclosureAgreementTemplate
from .serializers import (
    DataDisclosureAgreementSerializer,
    DataDisclosureAgreementsSerializer,
    DataDisclosureAgreementTemplateSerializer,
    DataDisclosureAgreementTemplatesSerializer,
)


class DataDisclosureAgreementView(APIView):
    """
    API View for retrieving and deleting individual Data Disclosure Agreements.

    Business Purpose:
        Provides access to specific DDA details for a Data Source. Supports
        versioning to allow retrieval of historical agreement versions for
        audit and compliance purposes.

    Authentication:
        - Requires authenticated user (IsAuthenticated permission)
        - User must be associated with a valid Data Source

    Business Rules:
        - DDAs are scoped to the requesting Data Source
        - If no version specified, returns the latest version
        - Deleting a DDA removes all its version history
    """

    serializer_class = DataDisclosureAgreementSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get(
        self,
        request: Request,
        dataDisclosureAgreementId: str,
        *args: Any,
        **kwargs: Any,
    ) -> JsonResponse:
        """
        Retrieve a specific Data Disclosure Agreement.

        Business Logic:
            Fetches a DDA by its template ID. Supports optional version parameter
            to retrieve specific historical versions for audit purposes.

        Request:
            GET /data-disclosure-agreements/{dataDisclosureAgreementId}/
            Query Parameters:
                - version (str, optional): Specific version to retrieve

        Path Parameters:
            - dataDisclosureAgreementId (str): Template ID of the DDA

        Response (200 OK):
            {
                "dataDisclosureAgreement": {
                    "@context": [...],
                    "@type": str,
                    "@id": str,
                    "version": str,
                    "status": str,
                    "isLatestVersion": bool,
                    ... (full DDA record structure)
                }
            }

        Error Responses:
            - 400: Data source not found or DDA not found

        Business Rules:
            - Returns the latest version if no version parameter specified
            - Only DDAs belonging to the user's Data Source are accessible
        """
        version_param = request.query_params.get("version")
        datasource, error_response = get_datasource_or_400(request.user)
        if error_response:
            return error_response

        try:
            data_disclosure_agreement: DataDisclosureAgreement | None
            if version_param:
                data_disclosure_agreement = DataDisclosureAgreement.objects.get(
                    templateId=dataDisclosureAgreementId,
                    dataSourceId=datasource,
                    version=version_param,
                )
            else:
                data_disclosure_agreement = DataDisclosureAgreement.objects.filter(
                    templateId=dataDisclosureAgreementId, dataSourceId=datasource
                ).last()
        except DataDisclosureAgreement.DoesNotExist:
            return JsonResponse(
                {"error": "Data Disclosure Agreement not found"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = self.serializer_class(
            data_disclosure_agreement, context={"request": request}
        )
        dda = serializer.data["dataDisclosureAgreementRecord"]
        dda["status"] = serializer.data["status"]
        dda["isLatestVersion"] = serializer.data["isLatestVersion"]
        response_data = {
            "dataDisclosureAgreement": dda,
        }

        return JsonResponse(response_data)

    def delete(
        self,
        request: Request,
        dataDisclosureAgreementId: str,
        *args: Any,
        **kwargs: Any,
    ) -> JsonResponse:
        """
        Delete a Data Disclosure Agreement and all its versions.

        Business Logic:
            Permanently removes a DDA and all its historical versions from
            the system. This is a destructive operation that cannot be undone.

        Request:
            DELETE /data-disclosure-agreements/{dataDisclosureAgreementId}/

        Path Parameters:
            - dataDisclosureAgreementId (str): Template ID of the DDA to delete

        Response:
            - 204 No Content: DDA successfully deleted

        Error Responses:
            - 400: Data source not found or DDA not found

        Business Rules:
            - All versions of the DDA are deleted (cascade delete)
            - Only DDAs belonging to the user's Data Source can be deleted
            - This operation is irreversible
        """
        datasource, error_response = get_datasource_or_400(request.user)
        if error_response:
            return error_response

        try:
            data_disclosure_agreement_revisions = (
                DataDisclosureAgreement.objects.filter(
                    templateId=dataDisclosureAgreementId, dataSourceId=datasource
                )
            )
        except DataDisclosureAgreement.DoesNotExist:
            return JsonResponse(
                {"error": "Data Disclosure Agreement not found"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Delete the data disclosure agreement
        data_disclosure_agreement_revisions.delete()

        return JsonResponse({}, status=status.HTTP_204_NO_CONTENT)


class DataDisclosureAgreementsView(APIView):
    """
    API View for listing all Data Disclosure Agreements for a Data Source.

    Business Purpose:
        Provides a paginated list of all DDAs owned by the authenticated
        Data Source. Supports filtering by status for workflow management.

    Authentication:
        - Requires authenticated user (IsAuthenticated permission)
        - User must be associated with a valid Data Source

    Business Rules:
        - Returns only the latest version of each unique DDA template
        - Can filter by status (unlisted, awaitingForApproval, approved, listed)
        - Results are paginated for performance
    """

    serializer_class = DataDisclosureAgreementsSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request: Request, *args: Any, **kwargs: Any) -> JsonResponse:
        """
        List all Data Disclosure Agreements for the authenticated Data Source.

        Business Logic:
            Retrieves all unique DDAs grouped by template ID. For each template,
            returns only the latest version unless filtered by status.

        Request:
            GET /data-disclosure-agreements/
            Query Parameters:
                - status (str, optional): Filter by DDA status
                - page (int): Page number for pagination
                - limit (int): Number of items per page

        Response (200 OK):
            {
                "dataDisclosureAgreements": [...],
                "pagination": {
                    "currentPage": int,
                    "totalItems": int,
                    "totalPages": int,
                    "limit": int,
                    "hasPrevious": bool,
                    "hasNext": bool
                }
            }

        Error Responses:
            - 400: Data source not found

        Business Rules:
            - Groups DDAs by templateId and returns latest version of each
            - Status filter overrides the isLatestVersion filter
        """
        # Get the 'status' query parameter
        status_param = request.query_params.get("status")

        datasource, error_response = get_datasource_or_400(request.user)
        if error_response:
            return error_response

        if datasource is None:
            return JsonResponse(
                {"error": "Data source not found"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        data_disclosure_agreements_template_ids = (
            DataDisclosureAgreement.list_unique_dda_template_ids_for_a_data_source(
                data_source_id=str(datasource.id)
            )
        )

        ddas: list[Any] = []

        temp_dda: dict[str, Any] = {}
        for dda_template_id in data_disclosure_agreements_template_ids:
            filter_kwargs: dict[str, Any] = {
                "templateId": dda_template_id,
                "dataSourceId": datasource,
            }
            if status_param:
                filter_kwargs["status"] = status_param
            else:
                filter_kwargs["isLatestVersion"] = True

            latest_dda_for_template_id = (
                DataDisclosureAgreement.objects.filter(**filter_kwargs)
                .order_by("-createdAt")
                .first()
            )

            serializer = self.serializer_class(latest_dda_for_template_id)
            temp_dda = serializer.data["dataDisclosureAgreementRecord"]

            if temp_dda:
                temp_dda["status"] = serializer.data["status"]
                temp_dda["isLatestVersion"] = serializer.data["isLatestVersion"]
                ddas.append(temp_dda)

        paginated_ddas, pagination_data = paginate_queryset(ddas, request)

        response_data = {
            "dataDisclosureAgreements": paginated_ddas,
            "pagination": pagination_data,
        }
        return JsonResponse(response_data)


# Defines the valid state machine transitions for DDA status
# Format: (current_status, target_status)
# Business Rules:
#   - unlisted -> awaitingForApproval: Submit for approval
#   - approved -> listed: Publish approved DDA
#   - rejected -> awaitingForApproval: Resubmit after rejection
#   - listed -> unlisted: Unpublish/delist a DDA
ALLOWED_DDA_STATUS_TRANSITIONS = {
    ("unlisted", "awaitingForApproval"),
    ("approved", "listed"),
    ("rejected", "awaitingForApproval"),
    ("listed", "unlisted"),
}


def validate_update_dda_request_body(
    to_be_updated_status: str, current_status: str
) -> bool:
    """
    Validate if a DDA status transition is allowed.

    Business Logic:
        Enforces the DDA lifecycle state machine. Only specific status
        transitions are permitted to maintain workflow integrity.

    Args:
        to_be_updated_status: The target status to transition to
        current_status: The current status of the DDA

    Returns:
        bool: True if the transition is valid, False otherwise

    Valid Transitions:
        - unlisted -> awaitingForApproval (submit for review)
        - approved -> listed (publish the agreement)
        - rejected -> awaitingForApproval (resubmit for review)
        - listed -> unlisted (take down published agreement)
    """
    return (current_status, to_be_updated_status) in ALLOWED_DDA_STATUS_TRANSITIONS


class DataDisclosureAgreementUpdateView(APIView):
    """
    API View for updating the status of a Data Disclosure Agreement.

    Business Purpose:
        Manages the DDA lifecycle by allowing status transitions. This is
        critical for the approval workflow where DDAs move through states
        like unlisted, awaitingForApproval, approved, and listed.

    Authentication:
        - Requires authenticated user (IsAuthenticated permission)
        - User must be associated with a valid Data Source

    Business Rules:
        - Only the latest version of a DDA can have its status updated
        - Status transitions must follow the defined state machine
        - Invalid transitions are rejected with an error
    """

    permission_classes = [permissions.IsAuthenticated]

    def put(
        self,
        request: Request,
        dataDisclosureAgreementId: str,
        *args: Any,
        **kwargs: Any,
    ) -> JsonResponse:
        """
        Update the status of a Data Disclosure Agreement.

        Business Logic:
            Transitions a DDA from its current status to a new status,
            following the allowed state machine transitions.

        Request:
            PUT /data-disclosure-agreements/{dataDisclosureAgreementId}/status/
            Body:
                {
                    "status": str  # Target status
                }

        Path Parameters:
            - dataDisclosureAgreementId (str): Template ID of the DDA

        Response:
            - 204 No Content: Status successfully updated

        Error Responses:
            - 400: Invalid status transition, DDA not found, or Data Source not found

        Business Rules:
            - Only latest version DDAs can be updated
            - Valid transitions: unlisted->awaitingForApproval, approved->listed,
              rejected->awaitingForApproval, listed->unlisted
            - The DDA record is also updated to maintain consistency
        """
        to_be_updated_status: str = request.data.get("status", "")

        datasource, error_response = get_datasource_or_400(request.user)
        if error_response:
            return error_response

        try:
            data_disclosure_agreement = DataDisclosureAgreement.objects.get(
                templateId=dataDisclosureAgreementId,
                dataSourceId=datasource,
                isLatestVersion=True,
            )
        except DataDisclosureAgreement.DoesNotExist:
            return JsonResponse(
                {"error": "Data Disclosure Agreement not found"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        is_valid_dda_status = validate_update_dda_request_body(
            to_be_updated_status=to_be_updated_status,
            current_status=data_disclosure_agreement.status,
        )

        if is_valid_dda_status:
            dda_record = data_disclosure_agreement.dataDisclosureAgreementRecord
            dda_record["status"] = to_be_updated_status
            data_disclosure_agreement.status = to_be_updated_status
            data_disclosure_agreement.dataDisclosureAgreementRecord = dda_record
            data_disclosure_agreement.save()

            return JsonResponse({}, status=status.HTTP_204_NO_CONTENT)
        else:
            return JsonResponse(
                {"error": "Data Disclosure Agreement status cannot be updated"},
                status=status.HTTP_400_BAD_REQUEST,
            )


class DataDisclosureAgreementTempleteView(APIView):
    """
    API View for retrieving individual DDA Templates.

    Business Purpose:
        Provides access to DDA templates owned by an Organisation. Templates
        are the editable drafts that define the terms of data sharing agreements
        before they are published.

    Authentication:
        - Requires authenticated user (IsAuthenticated permission)
        - User must be associated with a valid Organisation

    Business Rules:
        - Archived templates are excluded from results
        - Supports version-specific retrieval for audit purposes
        - Returns the latest non-archived version by default
    """

    serializer_class = DataDisclosureAgreementTemplateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get(
        self,
        request: Request,
        dataDisclosureAgreementId: str,
        *args: Any,
        **kwargs: Any,
    ) -> JsonResponse:
        """
        Retrieve a specific DDA Template.

        Business Logic:
            Fetches a DDA template by its ID, excluding archived versions.
            Supports optional version parameter for historical access.

        Request:
            GET /data-disclosure-agreement-templates/{dataDisclosureAgreementId}/
            Query Parameters:
                - version (str, optional): Specific version to retrieve

        Path Parameters:
            - dataDisclosureAgreementId (str): Template ID of the DDA

        Response (200 OK):
            {
                "dataDisclosureAgreement": {
                    ... (full DDA template structure),
                    "status": str,
                    "isLatestVersion": bool,
                    "createdAt": datetime,
                    "updatedAt": datetime,
                    "tags": list
                }
            }

        Error Responses:
            - 400: Organisation not found or DDA template not found
            - 404: Active DDA template not found

        Business Rules:
            - Archived templates are never returned
            - If no version specified, returns the latest non-archived version
        """
        version_param = request.query_params.get("version")
        organisation, error_response = get_organisation_or_400(request.user)
        if error_response:
            return error_response

        try:
            dda_template: DataDisclosureAgreementTemplate | None
            if version_param:
                dda_template = DataDisclosureAgreementTemplate.objects.exclude(
                    status="archived"
                ).get(
                    templateId=dataDisclosureAgreementId,
                    organisationId=organisation,
                    version=version_param,
                )
            else:
                dda_template = (
                    DataDisclosureAgreementTemplate.objects.exclude(status="archived")
                    .filter(
                        templateId=dataDisclosureAgreementId,
                        organisationId=organisation,
                    )
                    .last()
                )

                if not dda_template:
                    return JsonResponse(
                        {"error": "Active Data Disclosure Agreement not found"},
                        status=status.HTTP_404_NOT_FOUND,
                    )

        except DataDisclosureAgreementTemplate.DoesNotExist:
            return JsonResponse(
                {"error": "Data Disclosure Agreement not found"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = self.serializer_class(dda_template, context={"request": request})
        dda = serializer.data["dataDisclosureAgreementRecord"]
        dda["status"] = serializer.data["status"]
        dda["isLatestVersion"] = serializer.data["isLatestVersion"]
        dda["createdAt"] = serializer.data["createdAt"]
        dda["updatedAt"] = serializer.data["updatedAt"]
        dda["tags"] = serializer.data["tags"]
        response_data = {
            "dataDisclosureAgreement": dda,
        }

        return JsonResponse(response_data)


class DataDisclosureAgreementTemplatesView(APIView):
    """
    API View for listing all DDA Templates for an Organisation.

    Business Purpose:
        Provides a comprehensive view of all DDA templates owned by an
        Organisation, including their revision history. This enables
        template management and version control for data sharing agreements.

    Authentication:
        - Requires authenticated user (IsAuthenticated permission)
        - User must be associated with a valid Organisation

    Business Rules:
        - Archived templates are excluded from results
        - Each template includes its revision history
        - Supports filtering by status
        - Results are paginated for performance
    """

    serializer_class = DataDisclosureAgreementTemplatesSerializer
    permission_classes = [permissions.IsAuthenticated]

    def _build_latest_dda_payload(
        self, ddas_for_template: list[DataDisclosureAgreementTemplate]
    ) -> dict[str, Any] | None:
        """
        Build a payload containing the latest DDA template with its revisions.

        Business Logic:
            Constructs a comprehensive response object that includes the latest
            version of a DDA template along with all its historical revisions.
            This provides a complete audit trail for compliance purposes.

        Args:
            ddas_for_template: List of all DDA template versions for a template ID

        Returns:
            dict containing the latest DDA data with embedded revisions, or None
            if no valid templates exist

        Business Rules:
            - Only the latest version is marked as isLatestVersion=True
            - Revisions are sorted by createdAt in descending order
            - Archived versions are excluded from the input
        """
        if not ddas_for_template:
            return None

        latest_dda = next(
            (dda for dda in ddas_for_template if dda.isLatestVersion), None
        )
        if not latest_dda:
            return None

        latest_serializer = self.serializer_class(latest_dda)
        latest_dda_data = latest_serializer.data["dataDisclosureAgreementRecord"]
        latest_dda_data["status"] = latest_serializer.data["status"]
        latest_dda_data["isLatestVersion"] = True
        latest_dda_data["createdAt"] = latest_serializer.data["createdAt"]
        latest_dda_data["updatedAt"] = latest_serializer.data["updatedAt"]
        latest_dda_data["tags"] = latest_serializer.data["tags"]

        revisions = []
        for dda in ddas_for_template:
            if dda.id != latest_dda.id:  # Skip the latest DDA
                serializer = self.serializer_class(dda)
                revision_data = serializer.data["dataDisclosureAgreementRecord"]
                revision_data["status"] = serializer.data["status"]
                revision_data["isLatestVersion"] = False
                revision_data["version"] = dda.version
                revision_data["createdAt"] = dda.createdAt
                revision_data["updatedAt"] = dda.updatedAt
                revisions.append(revision_data)

        latest_dda_data["revisions"] = sorted(
            revisions, key=lambda x: x["createdAt"], reverse=True
        )
        return dict(latest_dda_data)

    def get(self, request: Request, *args: Any, **kwargs: Any) -> JsonResponse:
        """
        List all DDA Templates for the authenticated Organisation.

        Business Logic:
            Retrieves all unique DDA templates grouped by template ID.
            Each template includes its complete revision history for
            audit and compliance purposes.

        Request:
            GET /data-disclosure-agreement-templates/
            Query Parameters:
                - status (str, optional): Filter by template status
                - page (int): Page number for pagination
                - limit (int): Number of items per page

        Response (200 OK):
            {
                "dataDisclosureAgreements": [
                    {
                        ... (DDA template fields),
                        "status": str,
                        "isLatestVersion": bool,
                        "revisions": [...]
                    }
                ],
                "pagination": {...}
            }

        Error Responses:
            - 400: Organisation not found

        Business Rules:
            - Archived templates are excluded
            - Each template includes its revision history
            - Results are paginated for performance
        """
        # Get the 'status' query parameter
        status_param = request.query_params.get("status")

        organisation, error_response = get_organisation_or_400(request.user)
        if error_response:
            return error_response

        if organisation is None:
            return JsonResponse(
                {"error": "Organisation not found"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        data_disclosure_agreements_template_ids = DataDisclosureAgreementTemplate.list_unique_dda_template_ids_for_a_data_source(
            data_source_id=str(organisation.id)
        )

        ddas: list[dict[str, Any]] = []

        for dda_template_id in data_disclosure_agreements_template_ids:
            filter_kwargs: dict[str, Any] = {
                "templateId": dda_template_id,
                "organisationId": organisation,
            }
            if status_param:
                filter_kwargs["status"] = status_param

            # Get all non-archived DDAs for this template ID
            ddas_for_template = list(
                DataDisclosureAgreementTemplate.objects.exclude(
                    status="archived"
                ).filter(**filter_kwargs)
            )

            latest_dda_data = self._build_latest_dda_payload(ddas_for_template)
            if not latest_dda_data:
                continue
            ddas.append(latest_dda_data)

        paginated_ddas, pagination_data = paginate_queryset(ddas, request)

        response_data = {
            "dataDisclosureAgreements": paginated_ddas,
            "pagination": pagination_data,
        }
        return JsonResponse(response_data)


class DataDisclosureAgreementTemplateUpdateView(APIView):
    """
    API View for updating the status of a DDA Template.

    Business Purpose:
        Manages the DDA template lifecycle by allowing status transitions.
        When a template is listed, previous versions are automatically
        unlisted to ensure only one active version is published.

    Authentication:
        - Requires authenticated user (IsAuthenticated permission)
        - User must be associated with a valid Organisation

    Business Rules:
        - Only the latest non-archived version can be updated
        - When listing a template, previous versions are set to 'unlisted'
        - Status transitions must follow the defined state machine
    """

    permission_classes = [permissions.IsAuthenticated]

    def put(
        self,
        request: Request,
        dataDisclosureAgreementId: str,
        *args: Any,
        **kwargs: Any,
    ) -> JsonResponse:
        """
        Update the status of a DDA Template.

        Business Logic:
            Transitions a DDA template from its current status to a new status.
            Special handling when transitioning to 'listed' status - all
            previous versions are automatically unlisted.

        Request:
            PUT /data-disclosure-agreement-templates/{dataDisclosureAgreementId}/status/
            Body:
                {
                    "status": str  # Target status
                }

        Path Parameters:
            - dataDisclosureAgreementId (str): Template ID of the DDA

        Response:
            - 204 No Content: Status successfully updated

        Error Responses:
            - 400: Invalid status transition, template not found, or Organisation not found

        Business Rules:
            - Only the latest non-archived version can be updated
            - When status changes to 'listed', previous versions become 'unlisted'
            - Archived versions remain archived (not affected by listing)
            - The template record is also updated to maintain consistency
        """
        dda_template_id = dataDisclosureAgreementId

        to_be_updated_status: str = request.data.get("status", "")

        organisation, error_response = get_organisation_or_400(request.user)
        if error_response:
            return error_response

        try:
            data_disclosure_agreement = DataDisclosureAgreementTemplate.objects.exclude(
                status="archived"
            ).get(
                templateId=dataDisclosureAgreementId,
                organisationId=organisation,
                isLatestVersion=True,
            )
        except DataDisclosureAgreementTemplate.DoesNotExist:
            return JsonResponse(
                {"error": "Data Disclosure Agreement not found"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        is_valid_dda_status = validate_update_dda_request_body(
            to_be_updated_status=to_be_updated_status,
            current_status=data_disclosure_agreement.status,
        )

        if is_valid_dda_status:
            if to_be_updated_status == "listed":
                # Iterate through existing DDAs and mark `isLatestVersion=false`
                existing_ddas = DataDisclosureAgreementTemplate.objects.filter(
                    templateId=dda_template_id,
                    organisationId=organisation,
                    isLatestVersion=False,
                )
                for existing_dda in existing_ddas:
                    if existing_dda.status != "archived":
                        existing_dda.status = "unlisted"
                    existing_dda.save()
            dda_record = data_disclosure_agreement.dataDisclosureAgreementRecord
            dda_record["status"] = to_be_updated_status
            data_disclosure_agreement.status = to_be_updated_status
            data_disclosure_agreement.dataDisclosureAgreementRecord = dda_record
            data_disclosure_agreement.save()

            return JsonResponse({}, status=status.HTTP_204_NO_CONTENT)
        else:
            return JsonResponse(
                {"error": "Data Disclosure Agreement status cannot be updated"},
                status=status.HTTP_400_BAD_REQUEST,
            )


class DataDisclosureAgreementTemplateTagsView(APIView):
    """
    API View for managing tags on DDA Templates.

    Business Purpose:
        Allows organisations to categorize their DDA templates with custom
        tags for easier discovery, filtering, and organization. Tags are
        free-form strings that can represent categories, topics, or other
        classification schemes.

    Authentication:
        - Requires authenticated user (IsAuthenticated permission)
        - User must be associated with a valid Organisation

    Business Rules:
        - Only the latest non-archived version can have tags updated
        - Tags must be a list of strings
        - Empty tag lists are allowed (to clear all tags)
    """

    permission_classes = [permissions.IsAuthenticated]

    def put(
        self,
        request: Request,
        dataDisclosureAgreementId: str,
        *args: Any,
        **kwargs: Any,
    ) -> JsonResponse:
        """
        Update tags for a DDA Template.

        Business Logic:
            Replaces all existing tags on a DDA template with the provided
            list of tags. This is a full replacement, not a merge operation.

        Request:
            PUT /data-disclosure-agreement-templates/{dataDisclosureAgreementId}/tags/
            Body:
                {
                    "tags": ["tag1", "tag2", ...]
                }

        Path Parameters:
            - dataDisclosureAgreementId (str): Template ID of the DDA

        Response (200 OK):
            {
                "tags": ["tag1", "tag2", ...]
            }

        Error Responses:
            - 400: Missing tags field, invalid format, template not found,
                   or Organisation not found

        Business Rules:
            - Only latest non-archived version can be updated
            - All tags must be strings
            - Replaces existing tags entirely (not additive)
        """
        tags = request.data.get("tags")

        if tags is None:
            return JsonResponse(
                {"error": "tags field is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not isinstance(tags, list):
            return JsonResponse(
                {"error": "tags must be a list of strings"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Validate all items are strings
        if not all(isinstance(tag, str) for tag in tags):
            return JsonResponse(
                {"error": "All tags must be strings"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        organisation, error_response = get_organisation_or_400(request.user)
        if error_response:
            return error_response

        try:
            data_disclosure_agreement = DataDisclosureAgreementTemplate.objects.exclude(
                status="archived"
            ).get(
                templateId=dataDisclosureAgreementId,
                organisationId=organisation,
                isLatestVersion=True,
            )
        except DataDisclosureAgreementTemplate.DoesNotExist:
            return JsonResponse(
                {"error": "Data Disclosure Agreement not found"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        data_disclosure_agreement.tags = tags
        data_disclosure_agreement.save()

        return JsonResponse({"tags": tags}, status=status.HTTP_200_OK)


class DataDisclosureAgreementHistoriesView(APIView):
    """
    API View for listing DDA Record History entries.

    Business Purpose:
        Provides an audit trail of all DDA record activities for a specific
        DDA template. This is essential for compliance, monitoring data
        sharing activities, and tracking consent changes over time.

    Authentication:
        - Requires authenticated user (IsAuthenticated permission)
        - User must be associated with a valid Organisation

    Business Rules:
        - History records are sorted by update date (most recent first)
        - Results are paginated for performance
        - Only history for the organisation's templates is accessible
    """

    serializer_class = DataDisclosureAgreementRecordHistorySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get(
        self,
        request: Request,
        dataDisclosureAgreementId: str,
        *args: Any,
        **kwargs: Any,
    ) -> JsonResponse:
        """
        List all history records for a specific DDA Template.

        Business Logic:
            Retrieves the complete audit trail of DDA record activities,
            including sign/unsign events, for a specific DDA template.

        Request:
            GET /data-disclosure-agreement-templates/{dataDisclosureAgreementId}/histories/
            Query Parameters:
                - page (int): Page number for pagination
                - limit (int): Number of items per page

        Path Parameters:
            - dataDisclosureAgreementId (str): Template ID of the DDA

        Response (200 OK):
            {
                "dataDisclosureAgreementRecordHistory": [...],
                "pagination": {...}
            }

        Error Responses:
            - 400: Organisation not found

        Business Rules:
            - Records are sorted by updatedAt in descending order
            - Only records belonging to the organisation are returned
        """
        dda_template_id = dataDisclosureAgreementId

        organisation, error_response = get_organisation_or_400(request.user)
        if error_response:
            return error_response

        try:
            dda_records_qs = DataDisclosureAgreementRecordHistory.objects.filter(
                organisationId=organisation,
                dataDisclosureAgreementTemplateId=dda_template_id,
            ).order_by("-updatedAt")
        except DataDisclosureAgreementRecordHistory.DoesNotExist:
            dda_records_qs = DataDisclosureAgreementRecordHistory.objects.none()

        serializer = self.serializer_class(dda_records_qs, many=True)

        dda_records, pagination_data = paginate_queryset(list(serializer.data), request)

        response_data = {
            "dataDisclosureAgreementRecordHistory": dda_records,
            "pagination": pagination_data,
        }
        return JsonResponse(response_data)


class DataDisclosureAgreementHistoryView(APIView):
    """
    API View for managing individual DDA Record History entries.

    Business Purpose:
        Allows deletion of specific history records. This may be needed
        for data retention compliance or cleaning up erroneous entries.
        Note: Exercise caution as history deletion affects audit trails.

    Authentication:
        - Requires authenticated user (IsAuthenticated permission)
        - User must be associated with a valid Organisation

    Business Rules:
        - Only history records belonging to the organisation can be deleted
        - The DDA template ID is validated for ownership
        - Deletion is permanent and cannot be undone
    """

    serializer_class = DataDisclosureAgreementRecordHistorySerializer
    permission_classes = [permissions.IsAuthenticated]

    def delete(
        self,
        request: Request,
        dataDisclosureAgreementId: str,
        pk: str,
        *args: Any,
        **kwargs: Any,
    ) -> JsonResponse:
        """
        Delete a specific history record.

        Business Logic:
            Permanently removes a DDA record history entry. Validates that
            the record belongs to the requesting organisation's DDA template.

        Request:
            DELETE /data-disclosure-agreement-templates/{dataDisclosureAgreementId}/histories/{pk}/

        Path Parameters:
            - dataDisclosureAgreementId (str): Template ID of the DDA
            - pk (str): Primary key of the history record to delete

        Response:
            - 204 No Content: History record successfully deleted

        Error Responses:
            - 400: Organisation not found
            - 404: History record not found or access denied

        Business Rules:
            - Record ownership is verified through organisation and template ID
            - Deletion is permanent and irreversible
            - May impact audit trail completeness
        """
        organisation, error_response = get_organisation_or_400(request.user)
        if error_response:
            return error_response

        try:
            record = DataDisclosureAgreementRecordHistory.objects.get(
                pk=pk,
                organisationId=organisation,
                dataDisclosureAgreementTemplateId=dataDisclosureAgreementId,
            )
            record.delete()
            return JsonResponse(
                {
                    "message": "Data disclosure agreement history record deleted successfully"
                },
                status=status.HTTP_204_NO_CONTENT,
            )
        except DataDisclosureAgreementRecordHistory.DoesNotExist:
            return JsonResponse(
                {
                    "error": "Data disclosure agreement history record not found or access denied"
                },
                status=status.HTTP_404_NOT_FOUND,
            )
