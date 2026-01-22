"""
Software Statement Serializers Module

This module provides Django REST Framework serializers for software statement
models. Software statements are verifiable credentials that attest to the
properties and capabilities of software applications (clients) operating
within the data space.

Serializers in this module handle:
- Software statement credentials issued to organisations
- Software statement templates defining credential schemas

Software statements are commonly used for:
- OAuth2/OpenID Connect Dynamic Client Registration
- B2B trust verification in data exchange scenarios
- Attestation of client application security properties
"""

from rest_framework import serializers

from software_statement.models import SoftwareStatement, SoftwareStatementTemplate


class SoftwareStatementSerializer(serializers.ModelSerializer[SoftwareStatement]):
    """
    Full serializer for Software Statement credentials.

    Serializes all fields of a software statement, which represents a
    verifiable credential certifying the properties of an organisation's
    software application within the data space. The credential includes
    the complete exchange history and current status.

    Serialized data includes:
    - Credential identifiers (id, credentialExchangeId)
    - Organisation reference (organisationId)
    - Credential lifecycle status (pending, issued, revoked, etc.)
    - Complete credential exchange history for audit purposes
    - Timestamps for tracking credential issuance and updates

    Typical use cases:
    - Organisation dashboard showing their software credentials
    - Credential verification endpoints
    - Admin views for managing issued credentials
    - Audit and compliance reporting on credential lifecycle

    Note: The credentialHistory field contains the full exchange record,
    including all messages and state transitions during the credential
    issuance process. This provides complete traceability for security
    and compliance requirements.
    """

    class Meta:
        model = SoftwareStatement
        # Include all fields for complete credential representation
        # The full history is essential for audit and verification
        fields = "__all__"


class SoftwareStatementTemplateSerializer(
    serializers.ModelSerializer[SoftwareStatementTemplate]
):
    """
    Full serializer for Software Statement Templates.

    Serializes software statement template configurations, which define
    the schema and properties for software statement credentials. Templates
    are created by data space administrators to standardize credential
    formats across participating organisations.

    Serialized data includes:
    - Template identifier (id)
    - Human-readable template name (softwareStatementTemplateName)
    - Credential definition reference (credentialDefinitionId)

    The credentialDefinitionId links to the credential definition in the
    verifiable credential infrastructure (e.g., Aries, DIDComm), which
    specifies the schema, attributes, and cryptographic properties.

    Typical use cases:
    - Admin interfaces for managing credential templates
    - Credential issuance workflows selecting appropriate templates
    - Configuration management for the data space trust framework
    """

    class Meta:
        model = SoftwareStatementTemplate
        # Include all fields for complete template configuration
        fields = "__all__"
