"""
Serializers for organisation management in the Data Space platform.

This module provides serializers for:
- Organisation profile data (name, sector, location, endpoints, etc.)
- Organisation identity verification and presentation records
- Organisation identity templates for credential verification
- Industry sectors for categorizing organisations
- Code of Conduct documents that organisations must agree to

Organisations in the data space represent entities (companies, institutions)
that participate in data exchange. They can act as data providers or consumers
and must verify their identity through credential presentations.
"""

from __future__ import annotations

from rest_framework import serializers

from .models import (
    CodeOfConduct,
    Organisation,
    OrganisationIdentity,
    OrganisationIdentityTemplate,
    Sector,
)


class OrganisationSerializer(serializers.ModelSerializer):  # type: ignore[type-arg]
    """
    Serializer for Organisation profile data.

    Handles the serialization of organisation information including basic
    profile data, branding assets, and various service endpoints. Used for
    both creating new organisations and retrieving organisation details.

    The verificationRequestURLPrefix field is an alias for owsBaseUrl,
    providing a more descriptive name for the Organisation Wallet Service
    base URL used in verification request flows.

    Fields:
        id: Unique identifier for the organisation (read-only)
        coverImageUrl: URL to the organisation's cover/banner image
        logoUrl: URL to the organisation's logo
        name: Organisation's display name
        sector: Industry sector the organisation belongs to
        location: Geographic location of the organisation
        policyUrl: URL to the organisation's privacy/data policy
        description: Text description of the organisation
        verificationRequestURLPrefix: Base URL for OWS verification requests
        openApiUrl: URL to the organisation's OpenAPI specification
        credentialOfferEndpoint: Endpoint for issuing credentials
        accessPointEndpoint: Data access point endpoint
        codeOfConduct: Reference to accepted Code of Conduct
        privacyDashboardUrl: URL to the organisation's privacy dashboard
    """

    # Map the internal owsBaseUrl field to a more descriptive API field name
    # This URL prefix is used when constructing verification request URLs
    verificationRequestURLPrefix = serializers.CharField(
        source="owsBaseUrl", read_only=True
    )

    class Meta:
        model = Organisation
        fields = [
            "id",
            "coverImageUrl",
            "logoUrl",
            "name",
            "sector",
            "location",
            "policyUrl",
            "description",
            "verificationRequestURLPrefix",
            "openApiUrl",
            "credentialOfferEndpoint",
            "accessPointEndpoint",
            "codeOfConduct",
            "privacyDashboardUrl",
        ]
        # ID is auto-generated and should not be set by clients
        read_only_fields = ["id"]


class OrganisationIdentitySerializer(serializers.ModelSerializer):  # type: ignore[type-arg]
    """
    Serializer for organisation identity verification records.

    Tracks the state and results of verifiable credential presentations
    used to verify an organisation's identity. Each organisation must
    complete identity verification before participating in the data space.

    Fields:
        id: Unique identifier for this identity record
        organisationId: Reference to the organisation being verified
        presentationExchangeId: External ID from the presentation exchange protocol
        presentationState: Current state of the verification (e.g., pending, verified)
        isPresentationVerified: Boolean indicating if verification succeeded
        presentationRecord: Full presentation record data (JSON)
    """

    class Meta:
        model = OrganisationIdentity
        fields = [
            "id",
            "organisationId",
            "presentationExchangeId",
            "presentationState",
            "isPresentationVerified",
            "presentationRecord",
        ]


class OrganisationIdentityTemplateSerializer(serializers.ModelSerializer):  # type: ignore[type-arg]
    """
    Serializer for organisation identity verification templates.

    Templates define the credential requirements and presentation request
    format used to verify organisation identities. The admin can configure
    what credentials are required for organisations to join the data space.

    This serializer exposes all fields from the model, as templates are
    managed by administrators and require full access to all properties.
    """

    class Meta:
        model = OrganisationIdentityTemplate
        fields = "__all__"


class SectorSerializer(serializers.ModelSerializer):  # type: ignore[type-arg]
    """
    Serializer for industry sector data.

    Sectors categorize organisations by their industry (e.g., Healthcare,
    Finance, Manufacturing). This helps users discover and filter
    organisations in the data space.

    Fields:
        id: Unique identifier for the sector (read-only)
        sectorName: Display name of the sector
    """

    class Meta:
        model = Sector
        fields = ["id", "sectorName"]
        # ID is auto-generated and should not be set by clients
        read_only_fields = ["id"]


class CodeOfConductSerializer(serializers.ModelSerializer):  # type: ignore[type-arg]
    """
    Serializer for Code of Conduct documents.

    The Code of Conduct is a PDF document that organisations must accept
    before joining the data space. Only one Code of Conduct can be active
    at a time, but historical versions are retained.

    The PDF file content is stored in the database (not serialized here)
    and served through a separate download endpoint.

    Fields:
        id: Unique identifier for the document (read-only)
        pdfFileName: Original filename of the uploaded PDF (read-only)
        isActive: Whether this is the currently active Code of Conduct
        createdAt: Timestamp when the document was uploaded (read-only)
        updatedAt: Timestamp of last modification (read-only)
    """

    class Meta:
        model = CodeOfConduct
        fields = ["id", "pdfFileName", "isActive", "createdAt", "updatedAt"]
        # These fields are managed by the system, not user input
        read_only_fields = ["id", "pdfFileName", "createdAt", "updatedAt"]
