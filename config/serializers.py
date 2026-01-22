"""
Serializers for data source configuration and verification in the Data Space platform.

This module provides serializers for:
- Data source profiles (external data providers connected to organisations)
- Verification records for data source credential presentations
- Verification templates defining credential requirements for data sources

Data sources represent external systems or services that provide data within
the data space. Each data source must be verified through credential
presentations before it can participate in data exchanges.
"""

from __future__ import annotations

from rest_framework import serializers

from .models import DataSource, Verification, VerificationTemplate


class VerificationSerializer(serializers.ModelSerializer):  # type: ignore[type-arg]
    """
    Serializer for data source verification records.

    Tracks the state and results of verifiable credential presentations
    used to verify a data source's credentials. Each data source must
    complete verification before being trusted to provide data.

    Fields:
        id: Unique identifier for this verification record
        dataSourceId: Reference to the data source being verified
        presentationExchangeId: External ID from the presentation exchange protocol
        presentationState: Current state of the verification process
        presentationRecord: Full presentation record data (JSON) containing
                          the credential details and verification proof
    """

    class Meta:
        model = Verification
        fields = [
            "id",
            "dataSourceId",
            "presentationExchangeId",
            "presentationState",
            "presentationRecord",
        ]


class DataSourceSerializer(serializers.ModelSerializer):  # type: ignore[type-arg]
    """
    Serializer for data source profile information.

    Data sources are external systems or services that provide data to
    organisations in the data space. This serializer handles their
    profile information including branding, location, and API endpoints.

    Data sources are similar to organisations but represent the actual
    data-providing services rather than the legal entities.

    Fields:
        id: Unique identifier for the data source (read-only)
        coverImageUrl: URL to the data source's cover/banner image
        logoUrl: URL to the data source's logo
        name: Display name of the data source
        sector: Industry sector the data source belongs to
        location: Geographic location of the data source
        policyUrl: URL to the data source's privacy/data policy
        description: Text description of the data source
        openApiUrl: URL to the data source's OpenAPI specification
    """

    class Meta:
        model = DataSource
        fields = [
            "id",
            "coverImageUrl",
            "logoUrl",
            "name",
            "sector",
            "location",
            "policyUrl",
            "description",
            "openApiUrl",
        ]
        # ID is auto-generated and should not be set by clients
        read_only_fields = ["id"]


class VerificationTemplateSerializer(serializers.ModelSerializer):  # type: ignore[type-arg]
    """
    Serializer for data source verification templates.

    Templates define the credential requirements and presentation request
    format used to verify data sources. Administrators configure these
    templates to specify what credentials data sources must present.

    This serializer exposes all fields from the model, as templates are
    managed by administrators and require full access to all properties.
    """

    class Meta:
        model = VerificationTemplate
        fields = "__all__"
