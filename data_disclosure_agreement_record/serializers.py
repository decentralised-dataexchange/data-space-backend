"""
Data Disclosure Agreement Record Serializers Module

This module provides Django REST Framework serializers for DDA subscription
and history tracking models. When organisations subscribe to Data Disclosure
Agreements, records are created to track the subscription state, consent
status, and historical changes.

Serializers in this module handle:
- Active subscription records (DataDisclosureAgreementRecord)
- Historical audit trail records (DataDisclosureAgreementRecordHistory)

These serializers are essential for:
- Tracking data consumer subscriptions to data provider agreements
- Maintaining audit trails for compliance and governance
- Providing evidence of consent for data protection regulations
"""

from rest_framework import serializers

from data_disclosure_agreement_record.models import (
    DataDisclosureAgreementRecord,
    DataDisclosureAgreementRecordHistory,
)


class DataDisclosureAgreementRecordsSerializer(
    serializers.ModelSerializer[DataDisclosureAgreementRecord]
):
    """
    Full serializer for Data Disclosure Agreement Record list views.

    Serializes all fields of active DDA subscription records, providing
    complete information about an organisation's subscription to a data
    sharing agreement. Includes the consent state, opt-in status, and
    the full agreement snapshot.

    The serialized data includes:
    - Subscription identifiers (id, dataDisclosureAgreementRecordId)
    - Agreement content snapshot (dataDisclosureAgreementRecord)
    - Consent state (state: unsigned/signed, optIn: true/false)
    - Template references for linking to the source agreement
    - Timestamps for audit trails

    Typical use cases:
    - Admin views listing all subscriptions
    - Organisation dashboards showing their active agreements
    - Compliance exports for regulatory reporting
    """

    class Meta:
        model = DataDisclosureAgreementRecord
        # Include all fields for complete subscription data
        fields = "__all__"


class DataDisclosureAgreementRecordSerializer(
    serializers.ModelSerializer[DataDisclosureAgreementRecord]
):
    """
    Full serializer for individual Data Disclosure Agreement Record views.

    Provides complete serialization of a single DDA subscription record.
    Currently identical to DataDisclosureAgreementRecordsSerializer but
    maintained as a separate class to allow for future customization of
    single-record vs. list representations.

    This serializer is typically used for:
    - Detailed view of a specific subscription
    - Create/update operations on subscription records
    - API responses for subscription management endpoints

    Note: Both this and DataDisclosureAgreementRecordsSerializer currently
    serialize all fields. They are kept separate to follow the pattern of
    having distinct serializers for list vs. detail views, allowing for
    independent evolution of each representation.
    """

    class Meta:
        model = DataDisclosureAgreementRecord
        # Include all fields for complete record representation
        fields = "__all__"


class DataDisclosureAgreementRecordHistorySerializer(
    serializers.ModelSerializer[DataDisclosureAgreementRecordHistory]
):
    """
    Full serializer for Data Disclosure Agreement Record History entries.

    Serializes historical snapshots of DDA subscriptions for audit and
    compliance purposes. Each history record represents a point-in-time
    state of a subscription, preserving the exact agreement terms and
    consent status at that moment.

    History records are immutable audit entries that capture:
    - The state of consent (signed/unsigned, optIn) at a specific time
    - The exact agreement content that was in effect
    - References to the template and revision for traceability
    - Timestamps marking when the snapshot was created

    Typical use cases:
    - Compliance audits requiring historical consent evidence
    - Dispute resolution showing what terms were agreed to
    - Analytics on subscription patterns and consent changes
    - Regulatory reporting for data protection authorities

    Note: History records include a foreign key to DataDisclosureAgreementTemplate,
    enabling efficient queries across all historical records for a specific
    agreement template.
    """

    class Meta:
        model = DataDisclosureAgreementRecordHistory
        # Include all fields for complete historical record
        # Essential for maintaining full audit trail integrity
        fields = "__all__"
