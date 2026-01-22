"""
Data Disclosure Agreement Serializers Module

This module provides Django REST Framework serializers for Data Disclosure Agreement
(DDA) models. DDAs are legally-binding contracts that govern data sharing between
organisations in the data space platform.

Serializers in this module handle:
- Full serialization of DDA records for administrative and detailed views
- Partial serialization for list views and status updates
- Both DataSource-based DDAs and Organisation-based DDA Templates

These serializers are used by the DDA API views to convert model instances to/from
JSON representations for the REST API.
"""

from rest_framework import serializers

from .models import DataDisclosureAgreement, DataDisclosureAgreementTemplate


class DataDisclosureAgreementsSerializer(
    serializers.ModelSerializer[DataDisclosureAgreement]
):
    """
    Full serializer for Data Disclosure Agreement list views.

    Serializes all fields of the DataDisclosureAgreement model, providing
    complete DDA information including the full JSON record, version history,
    and status. Used primarily for administrative interfaces and detailed
    API responses where the complete agreement data is required.

    Typical use cases:
    - Admin dashboard displaying all DDA details
    - Exporting DDA records for compliance audits
    - API endpoints requiring complete DDA information
    """

    class Meta:
        model = DataDisclosureAgreement
        # Include all model fields for complete serialization
        fields = "__all__"


class DataDisclosureAgreementSerializer(
    serializers.ModelSerializer[DataDisclosureAgreement]
):
    """
    Partial serializer for Data Disclosure Agreement summary views.

    Provides a lightweight representation of a DDA, including only the
    essential fields needed for status display and version tracking.
    Excludes metadata fields like timestamps and data source references
    to reduce payload size for list views.

    Serialized fields:
    - dataDisclosureAgreementRecord: The full JSON agreement content
    - status: Current lifecycle state (listed, unlisted, etc.)
    - isLatestVersion: Flag indicating if this is the current version

    Typical use cases:
    - Consumer-facing DDA listings in the marketplace
    - Status update responses
    - Version comparison views
    """

    class Meta:
        model = DataDisclosureAgreement
        # Selective fields for lightweight API responses
        # Includes the agreement content, status, and version flag
        fields = ["dataDisclosureAgreementRecord", "status", "isLatestVersion"]


class DataDisclosureAgreementTemplatesSerializer(
    serializers.ModelSerializer[DataDisclosureAgreementTemplate]
):
    """
    Full serializer for Data Disclosure Agreement Template list views.

    Serializes all fields of the DataDisclosureAgreementTemplate model,
    providing complete information for organisation-based DDA templates.
    This is the modern, organisation-centric approach to DDAs (as opposed
    to the DataSource-based approach).

    DDA Templates include additional fields not present in basic DDAs:
    - Template revision tracking for audit compliance
    - Tags for categorization and search
    - Updated timestamps for change detection

    Typical use cases:
    - Organisation admin views for managing their DDA templates
    - Data space admin review and approval workflows
    - Compliance audits requiring full template history
    """

    class Meta:
        model = DataDisclosureAgreementTemplate
        # Include all model fields for complete serialization
        fields = "__all__"


class DataDisclosureAgreementTemplateSerializer(
    serializers.ModelSerializer[DataDisclosureAgreementTemplate]
):
    """
    Partial serializer for Data Disclosure Agreement Template summary views.

    Provides a curated subset of template fields optimized for list views
    and status displays. Includes timestamp information for sorting and
    filtering, tags for categorization, and the essential agreement content.

    Serialized fields:
    - dataDisclosureAgreementRecord: The full JSON agreement content
    - status: Current lifecycle state (listed, unlisted, archived, etc.)
    - isLatestVersion: Flag indicating if this is the current version
    - createdAt: Timestamp when the template version was created
    - updatedAt: Timestamp of the most recent modification
    - tags: Categorization tags for filtering and search

    Typical use cases:
    - Consumer-facing template listings in the marketplace
    - Organisation dashboards showing their available templates
    - Search results with metadata for sorting and filtering
    """

    class Meta:
        model = DataDisclosureAgreementTemplate
        # Selective fields providing agreement content with metadata
        # Includes timestamps and tags for enhanced list view functionality
        fields = [
            "dataDisclosureAgreementRecord",
            "status",
            "isLatestVersion",
            "createdAt",
            "updatedAt",
            "tags",
        ]
