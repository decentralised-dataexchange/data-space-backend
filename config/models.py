"""
Config Models Module

This module defines data source entities and related verification models for the
data space platform. DataSource represents legacy or alternative data provider
configurations, while ImageModel provides centralized binary image storage.
The verification models support identity verification workflows for data sources.

Note: This module appears to be an older/alternative implementation. The primary
organisation model in organisation/models.py should be used for new features.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from django.db import models
from django.db.models import JSONField

from onboard.models import DataspaceUser


class ImageModel(models.Model):
    """
    Centralized storage for binary image data.

    This model provides a simple key-value store for image assets used throughout
    the platform. Images are stored as binary data directly in the database,
    ensuring portability and eliminating dependencies on external file storage.

    Usage:
        - Organisation logos and cover images reference this model via UUID
        - Profile pictures and other visual assets can be stored here
        - The UUID can be used in URLs to serve images through an API endpoint

    Design Considerations:
        - Binary storage in database is suitable for smaller images
        - For large-scale deployments, consider object storage (S3, GCS)
    """

    # Unique identifier for the image, used in URLs and foreign references
    id: models.UUIDField[UUID, UUID] = models.UUIDField(
        primary_key=True, default=uuid4, editable=False
    )

    # Raw binary data of the image file (PNG, JPEG, etc.)
    # No file type validation at the model level - handled in views
    image_data: models.BinaryField[bytes, bytes] = models.BinaryField()

    def __str__(self) -> str:
        return str(self.id)


class DataSource(models.Model):
    """
    Represents a data source (data provider) in the data space ecosystem.

    This model is similar to Organisation but specifically represents entities
    that provide data to the data space. It appears to be an older or parallel
    implementation to the Organisation model, potentially used for a different
    type of participant or legacy integrations.

    DataSources can expose their data through OpenAPI-documented APIs and
    establish connections with data consumers through the platform.

    Relationships:
        - One-to-One with DataspaceUser: Each data source has one admin
        - One-to-Many with Connection: A data source can have multiple connections
        - One-to-Many with DataDisclosureAgreement: A data source can have multiple DDAs
        - One-to-Many with Verification: A data source can have multiple verifications

    Note: Consider using Organisation model for new implementations, as it
    has more complete functionality including credential endpoints.
    """

    # Unique identifier for the data source (UUID v4)
    id: models.UUIDField[UUID, UUID] = models.UUIDField(
        primary_key=True, default=uuid4, editable=False
    )

    # URL to the data source's cover/banner image
    # Used for visual presentation in marketplace listings
    coverImageUrl: models.CharField[str, str] = models.CharField(max_length=255)

    # URL to the data source's logo
    # Displayed in headers and data source cards
    logoUrl: models.CharField[str, str] = models.CharField(max_length=255)

    # Official name of the data source
    # Displayed publicly in listings and agreements
    name: models.CharField[str, str] = models.CharField(max_length=100)

    # Industry sector the data source operates in
    # Used for categorization and marketplace filtering
    sector: models.CharField[str, str] = models.CharField(max_length=100)

    # Geographic location of the data source
    # Important for compliance and data residency considerations
    location: models.CharField[str, str] = models.CharField(max_length=100)

    # URL to the data source's privacy/data policy
    # Required for transparency in data sharing
    policyUrl: models.CharField[str, str] = models.CharField(max_length=255)

    # Detailed description of the data source and its offerings
    # Displayed in the data source's public profile
    description: models.TextField[str, str] = models.TextField()

    # Reference to internally stored cover image
    # Links to ImageModel for database-stored images
    coverImageId: models.UUIDField[UUID | None, UUID | None] = models.UUIDField(
        default=None, null=True, blank=True
    )

    # Reference to internally stored logo image
    # Links to ImageModel for database-stored images
    logoId: models.UUIDField[UUID | None, UUID | None] = models.UUIDField(
        default=None, null=True, blank=True
    )

    # The user who administers this data source
    # Has full control over data source configuration and agreements
    admin: models.OneToOneField[DataspaceUser, DataspaceUser] = models.OneToOneField(
        DataspaceUser, on_delete=models.CASCADE
    )

    # URL to the data source's OpenAPI specification
    # Enables API discovery and automated integration
    openApiUrl: models.CharField[str | None, str | None] = models.CharField(
        max_length=255, null=True, blank=True
    )

    # Timestamp when the data source was registered
    createdAt: models.DateTimeField[datetime, datetime] = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self) -> str:
        return str(self.name)


class Verification(models.Model):
    """
    Tracks identity verification for a data source.

    This model stores the results of verifiable presentation exchanges used to
    verify a data source's identity and credentials. Verification is essential
    for establishing trust in the data space ecosystem.

    The verification process follows the presentation exchange protocol from
    the Decentralized Identity Foundation (DIF), where data sources prove their
    identity by presenting verifiable credentials.

    Relationships:
        - Many-to-One with DataSource: Multiple verifications per data source
    """

    # Unique identifier for this verification record
    id: models.UUIDField[UUID, UUID] = models.UUIDField(
        primary_key=True, default=uuid4, editable=False
    )

    # Reference to the data source being verified
    # Cascade delete ensures verification records are removed with the data source
    dataSourceId: models.ForeignKey[DataSource, DataSource] = models.ForeignKey(
        DataSource, on_delete=models.CASCADE
    )

    # Unique identifier for the presentation exchange session
    # Used to correlate verification requests and responses
    presentationExchangeId: models.CharField[str, str] = models.CharField(
        max_length=50, unique=True
    )

    # Current state of the presentation exchange workflow
    # States include: request_sent, presentation_received, verified, etc.
    presentationState: models.CharField[str, str] = models.CharField(max_length=50)

    # Complete JSON record of the presentation exchange
    # Contains the verifiable presentation and verification results
    presentationRecord: JSONField[Any, Any] = JSONField()

    def __str__(self) -> str:
        return str(self.id)


class VerificationTemplate(models.Model):
    """
    Defines a template for data source verification requirements.

    This model stores configuration for verifying data sources in the data space.
    It specifies the credentials required, the trusted issuer, and links to the
    data agreement that governs the verification process.

    Templates enable consistent verification requirements across different
    data sources and can be customized for different verification scenarios.

    Usage:
        - Administrators create templates to define verification standards
        - Data sources are verified against these templates
        - Multiple templates allow for different verification tiers
    """

    # Unique identifier for this verification template
    id: models.UUIDField[UUID, UUID] = models.UUIDField(
        primary_key=True, default=uuid4, editable=False
    )

    # Human-readable name for the verification template
    # Describes the type of verification (e.g., "Standard Data Source Verification")
    verificationTemplateName: models.CharField[str | None, str | None] = (
        models.CharField(max_length=255, null=True, blank=True)
    )

    # Name of the credential issuer whose credentials are accepted
    # Identifies the trusted authority for this verification
    issuerName: models.CharField[str | None, str | None] = models.CharField(
        max_length=255, null=True, blank=True
    )

    # Geographic location of the credential issuer
    # Important for jurisdictional trust decisions
    issuerLocation: models.CharField[str | None, str | None] = models.CharField(
        max_length=255, null=True, blank=True
    )

    # URL to the issuer's logo for display in the verification UI
    issuerLogoUrl: models.CharField[str | None, str | None] = models.CharField(
        max_length=255, null=True, blank=True
    )

    # Reference to the data agreement governing this verification
    # Links verification requirements to a specific data agreement
    dataAgreementId: models.CharField[str | None, str | None] = models.CharField(
        max_length=255, null=True, blank=True
    )

    def __str__(self) -> str:
        return str(self.verificationTemplateName)
