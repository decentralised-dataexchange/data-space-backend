"""
Organisation Models Module

This module defines the core organisational entities within the data space platform.
Organisations are the primary actors in the data exchange ecosystem, capable of
acting as data providers, data consumers, or both. The module also includes
supporting models for organisation identity verification, identity templates,
industry sectors, and code of conduct management.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from django.db import models
from django.db.models import JSONField

from onboard.models import DataspaceUser


class Organisation(models.Model):
    """
    Represents an organisation registered in the data space ecosystem.

    Organisations are the fundamental business entities that participate in data
    exchange. They can act as data providers (sharing data through Data Disclosure
    Agreements), data consumers (subscribing to data from other organisations),
    or both. Each organisation has a designated administrator who manages the
    organisation's profile, data agreements, and connections.

    The organisation profile includes branding assets (logo, cover image), contact
    information, and technical endpoints for API integration and credential
    management in the decentralized identity framework.

    Relationships:
        - One-to-One with DataspaceUser: Each organisation has exactly one admin
        - One-to-Many with OrganisationIdentity: An organisation can have multiple verified identities
        - One-to-Many with DataDisclosureAgreementTemplate: Organisation can create multiple DDA templates
        - One-to-Many with B2BConnection: Organisation can have multiple B2B connections
        - One-to-Many with SoftwareStatement: Organisation can have multiple software statements
        - One-to-Many with OAuth2Clients: Organisation can register multiple OAuth2 clients

    Constraints:
        - Each user can only be admin of one organisation (OneToOne relationship)
    """

    # Unique identifier for the organisation (UUID v4)
    # Auto-generated and immutable after creation
    id: models.UUIDField[UUID, UUID] = models.UUIDField(
        primary_key=True, default=uuid4, editable=False
    )

    # URL to the organisation's cover/banner image for display in marketplace listings
    # Used for visual branding in the data space portal
    coverImageUrl: models.CharField[str, str] = models.CharField(max_length=255)

    # URL to the organisation's logo image
    # Displayed in headers, cards, and throughout the platform UI
    logoUrl: models.CharField[str, str] = models.CharField(max_length=255)

    # Official name of the organisation
    # Displayed publicly in listings and agreements
    name: models.CharField[str, str] = models.CharField(max_length=100)

    # Industry sector the organisation operates in (e.g., "Healthcare", "Finance")
    # Used for categorization and filtering in the marketplace
    sector: models.CharField[str, str] = models.CharField(max_length=100)

    # Geographic location or headquarters of the organisation
    # Important for compliance and jurisdictional considerations
    location: models.CharField[str, str] = models.CharField(max_length=100)

    # URL to the organisation's privacy policy or data governance policy
    # Required for transparency and compliance in data exchange
    policyUrl: models.CharField[str, str] = models.CharField(max_length=255)

    # Detailed description of the organisation and its data offerings
    # Displayed in the organisation's public profile
    description: models.TextField[str, str] = models.TextField()

    # Reference to the stored cover image in the ImageModel
    # Allows for internal image storage rather than external URLs
    coverImageId: models.UUIDField[UUID | None, UUID | None] = models.UUIDField(
        default=None, null=True, blank=True
    )

    # Reference to the stored logo image in the ImageModel
    # Allows for internal image storage rather than external URLs
    logoId: models.UUIDField[UUID | None, UUID | None] = models.UUIDField(
        default=None, null=True, blank=True
    )

    # The user who administers this organisation
    # Has full control over organisation settings and data agreements
    admin: models.OneToOneField[DataspaceUser, DataspaceUser] = models.OneToOneField(
        DataspaceUser, on_delete=models.CASCADE
    )

    # Base URL for OGC Web Services (OWS) if the organisation provides geospatial data
    # Used for WMS, WFS, and other OGC-compliant service endpoints
    owsBaseUrl: models.CharField[str | None, str | None] = models.CharField(
        max_length=255, null=True, blank=True
    )

    # URL to the organisation's OpenAPI specification document
    # Enables API discovery and integration with external systems
    openApiUrl: models.CharField[str | None, str | None] = models.CharField(
        max_length=255, null=True, blank=True
    )

    # Endpoint for receiving verifiable credential offers
    # Part of the decentralized identity infrastructure for credential issuance
    credentialOfferEndpoint: models.CharField[str | None, str | None] = (
        models.CharField(max_length=255, null=True, blank=True)
    )

    # Endpoint for the organisation's access point in the data space
    # Used for B2B data exchange and connector communication
    accessPointEndpoint: models.CharField[str | None, str | None] = models.CharField(
        max_length=255, null=True, blank=True
    )

    # Flag indicating whether the organisation has accepted the data space code of conduct
    # Required for full participation in the ecosystem
    codeOfConduct: models.BooleanField[bool, bool] = models.BooleanField(default=False)

    # URL to the organisation's privacy dashboard for data subjects
    # Enables individuals to manage their consent and data preferences
    privacyDashboardUrl: models.CharField[str | None, str | None] = models.CharField(
        max_length=255, null=True, blank=True
    )

    # Timestamp when the organisation was registered in the data space
    # Automatically set upon creation
    createdAt: models.DateTimeField[datetime, datetime] = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self) -> str:
        return str(self.name)


class OrganisationIdentity(models.Model):
    """
    Represents a verified identity for an organisation in the data space.

    This model stores the results of verifiable presentation exchanges used to
    establish the organisation's identity and credentials. In the decentralized
    identity framework, organisations must prove their identity through
    cryptographically verifiable presentations, which are then stored and tracked
    in this model.

    The verification process uses presentation exchange protocols to validate
    credentials issued by trusted authorities, ensuring that only legitimate
    organisations can participate in the data space.

    Relationships:
        - Many-to-One with Organisation: Multiple identity verifications can exist for one organisation
    """

    # Unique identifier for this identity record
    id: models.UUIDField[UUID, UUID] = models.UUIDField(
        primary_key=True, default=uuid4, editable=False
    )

    # Reference to the organisation this identity belongs to
    # An organisation can have multiple verified identities over time
    organisationId: models.ForeignKey[Organisation, Organisation] = models.ForeignKey(
        Organisation, on_delete=models.CASCADE
    )

    # Unique identifier for the presentation exchange session
    # Used to correlate requests and responses in the verification flow
    presentationExchangeId: models.CharField[str, str] = models.CharField(
        max_length=50, unique=True
    )

    # Current state of the presentation exchange (e.g., "request_sent", "verified", "abandoned")
    # Tracks the progress of the verification workflow
    presentationState: models.CharField[str, str] = models.CharField(max_length=50)

    # Flag indicating whether the presentation was successfully verified
    # True if all credential proofs were validated
    isPresentationVerified: models.BooleanField[bool, bool] = models.BooleanField(
        default=False
    )

    # Full JSON record of the presentation exchange
    # Contains the verifiable presentation and verification results
    presentationRecord: JSONField[Any, Any] = JSONField()

    # Timestamp when this identity verification was initiated
    createdAt: models.DateTimeField[datetime, datetime] = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self) -> str:
        return str(self.id)

    class Meta:
        verbose_name = "Organisation Identity"
        verbose_name_plural = "Organisation Identities"


class OrganisationIdentityTemplate(models.Model):
    """
    Defines a template for organisation identity verification.

    This model stores configuration for how organisations should be verified
    within the data space. It specifies which credentials are required and
    from which issuers, enabling consistent and standardized identity
    verification across all participating organisations.

    The template references a presentation definition that describes the
    exact credential types and attributes required for verification.

    Usage:
        Templates are created by data space administrators to define
        verification requirements for different types of organisations
        or membership tiers.
    """

    # Unique identifier for the template
    id: models.UUIDField[UUID, UUID] = models.UUIDField(
        primary_key=True, default=uuid4, editable=False
    )

    # Human-readable name for this verification template
    # Describes the type of verification (e.g., "Standard Organisation Verification")
    organisationIdentityTemplateName: models.CharField[str | None, str | None] = (
        models.CharField(max_length=255, null=True, blank=True)
    )

    # Name of the trusted issuer whose credentials are accepted
    # Identifies the authority that issues the required credentials
    issuerName: models.CharField[str | None, str | None] = models.CharField(
        max_length=255, null=True, blank=True
    )

    # Location/jurisdiction of the credential issuer
    # Important for regulatory compliance and trust establishment
    issuerLocation: models.CharField[str | None, str | None] = models.CharField(
        max_length=255, null=True, blank=True
    )

    # URL to the issuer's logo for display in the verification UI
    issuerLogoUrl: models.CharField[str | None, str | None] = models.CharField(
        max_length=255, null=True, blank=True
    )

    # Reference to the presentation definition in the credential system
    # Defines the exact requirements for the verifiable presentation
    presentationDefinitionId: models.CharField[str | None, str | None] = (
        models.CharField(max_length=255, null=True, blank=True)
    )

    def __str__(self) -> str:
        return str(self.organisationIdentityTemplateName)

    class Meta:
        verbose_name = "Organisation Identity Template"
        verbose_name_plural = "Organisation Identity Template"


class Sector(models.Model):
    """
    Represents an industry sector for organisation categorization.

    Sectors provide a standardized classification system for organisations
    within the data space. This enables filtering, search, and matching
    of organisations and data offerings by industry vertical.

    Examples include: Healthcare, Finance, Transportation, Energy, Agriculture, etc.

    Usage:
        - Organisations select their sector during registration
        - Data consumers can filter data offerings by sector
        - Analytics and reporting can be segmented by sector
    """

    # Unique identifier for the sector
    id: models.UUIDField[UUID, UUID] = models.UUIDField(
        primary_key=True, default=uuid4, editable=False
    )

    # Name of the industry sector (must be unique)
    # Used for display and selection in the organisation registration flow
    sectorName: models.CharField[str, str] = models.CharField(
        max_length=100, unique=True
    )

    def __str__(self) -> str:
        return str(self.sectorName)

    class Meta:
        verbose_name = "Organisation Sector"
        verbose_name_plural = "Organisation Sectors"


class CodeOfConduct(models.Model):
    """
    Represents the data space's Code of Conduct document.

    The Code of Conduct establishes the rules, ethical guidelines, and
    behavioral expectations for all participants in the data space. Organisations
    must accept the Code of Conduct before they can fully participate in
    data exchange activities.

    This model stores the PDF document content in the database, allowing for
    versioning and ensuring the document is always accessible even if external
    storage is unavailable.

    Business Rules:
        - Only one Code of Conduct can be active at a time
        - Organisations must re-accept if the Code of Conduct is updated
        - Historical versions are retained for audit purposes
    """

    # Unique identifier for this Code of Conduct version
    id: models.UUIDField[UUID, UUID] = models.UUIDField(
        primary_key=True, default=uuid4, editable=False
    )

    # Binary content of the PDF document
    # Stored directly in the database for reliability and portability
    pdfContent: models.BinaryField[bytes | None, bytes | None] = models.BinaryField(
        null=True, blank=True
    )

    # Original filename of the uploaded PDF
    # Preserved for download functionality
    pdfFileName: models.CharField[str | None, str | None] = models.CharField(
        max_length=255, null=True, blank=True
    )

    # Timestamp when this Code of Conduct version was created
    createdAt: models.DateTimeField[datetime, datetime] = models.DateTimeField(
        auto_now_add=True
    )

    # Timestamp when this Code of Conduct was last modified
    updatedAt: models.DateTimeField[datetime, datetime] = models.DateTimeField(
        auto_now=True
    )

    # Flag indicating whether this is the currently active Code of Conduct
    # Only one record should have isActive=True at any time
    isActive: models.BooleanField[bool, bool] = models.BooleanField(default=True)

    def __str__(self) -> str:
        return f"Code of Conduct - {self.updatedAt.strftime('%Y-%m-%d %H:%M')}"

    class Meta:
        verbose_name = "Code of Conduct"
        verbose_name_plural = "Code of Conduct"
        ordering = ["-updatedAt"]
