"""
Data Disclosure Agreement Record Models Module

This module defines models for tracking individual Data Disclosure Agreement (DDA)
subscriptions and their history. When an organisation (data consumer) subscribes
to a DDA from a data provider, a record is created to track the agreement state,
consent status, and any changes over time.

These records provide the audit trail and legal evidence for data sharing activities,
enabling compliance with data protection regulations and governance requirements.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from django.db import models
from jsonfield.fields import JSONField

from data_disclosure_agreement.models import DataDisclosureAgreementTemplate
from organisation.models import Organisation


class DataDisclosureAgreementRecord(models.Model):
    """
    Represents an active subscription to a Data Disclosure Agreement.

    When a data consumer organisation subscribes to a data provider's DDA,
    a record is created to track the subscription. This record captures the
    current state of the agreement (signed/unsigned), the opt-in status,
    and a snapshot of the agreement terms at the time of subscription.

    The record maintains the live state of the subscription and can be updated
    as the organisation modifies their consent preferences.

    Relationships:
        - Many-to-One with Organisation: The subscribing organisation (data consumer)

    Business Rules:
        - Each record tracks a unique subscription identified by dataDisclosureAgreementRecordId
        - The optIn flag indicates whether the organisation has actively consented
        - State transitions: unsigned -> signed (upon signature/consent)
        - Records can be updated when consent preferences change

    Note: For historical tracking of changes, see DataDisclosureAgreementRecordHistory.
    """

    class Meta:
        verbose_name = "Data Disclosure Agreement Record"
        verbose_name_plural = "Data Disclosure Agreement Record"

    # Possible states for the agreement record
    STATE_CHOICES = [
        ("unsigned", "unsigned"),  # Agreement not yet signed by the consumer
        ("signed", "signed"),  # Agreement has been signed/accepted
    ]

    # Unique identifier for this record in the database
    id: models.UUIDField[UUID, UUID] = models.UUIDField(
        primary_key=True, default=uuid4, editable=False
    )

    # Current signature state of the agreement
    # Unsigned records may be in negotiation or awaiting consent
    state: models.CharField[str, str] = models.CharField(
        max_length=255, choices=STATE_CHOICES, default="unsigned"
    )

    # Reference to the subscribing organisation (data consumer)
    # This is the organisation that is receiving/consuming the data
    organisationId: models.ForeignKey[Organisation, Organisation] = models.ForeignKey(
        Organisation, on_delete=models.CASCADE
    )

    # Complete JSON snapshot of the DDA at the time of subscription
    # Preserves the exact terms agreed to, even if the template is later updated
    dataDisclosureAgreementRecord: JSONField[Any, Any] = JSONField()

    # Reference to the DDA template this record is based on
    # Used to link back to the original agreement definition
    dataDisclosureAgreementTemplateId: models.CharField[str, str] = models.CharField(
        max_length=255, null=False
    )

    # Reference to the specific revision of the template
    # Ensures traceability to the exact version that was agreed to
    dataDisclosureAgreementTemplateRevisionId: models.CharField[str, str] = (
        models.CharField(max_length=255, null=False)
    )

    # Unique identifier for this subscription across the system
    # External reference that can be used in APIs and integrations
    dataDisclosureAgreementRecordId: models.CharField[str, str] = models.CharField(
        max_length=255, null=False
    )

    # Flag indicating active consent/opt-in status
    # True if the organisation has explicitly opted into data sharing
    # Can be toggled when the organisation withdraws or renews consent
    optIn: models.BooleanField[bool, bool] = models.BooleanField(default=False)

    # Timestamp when the subscription record was created
    createdAt: models.DateTimeField[datetime, datetime] = models.DateTimeField(
        auto_now_add=True
    )

    # Timestamp of the most recent update to this record
    # Updated when state, optIn, or other fields change
    updatedAt: models.DateTimeField[datetime, datetime] = models.DateTimeField(
        auto_now=True
    )

    def __str__(self) -> str:
        return str(self.id)


class DataDisclosureAgreementRecordHistory(models.Model):
    """
    Maintains historical records of DDA subscription changes.

    This model provides an audit trail for Data Disclosure Agreement
    subscriptions. Each time a subscription's state or consent status
    changes, a history record can be created to preserve the previous
    state for compliance and audit purposes.

    The history model includes a direct foreign key to the DDA template,
    enabling efficient queries to find all historical records for a
    specific agreement.

    Relationships:
        - Many-to-One with Organisation: The subscribing organisation
        - Many-to-One with DataDisclosureAgreementTemplate: The agreement template

    Business Rules:
        - History records are immutable once created
        - Each record represents a point-in-time snapshot of the subscription
        - Used for compliance audits, dispute resolution, and analytics
    """

    class Meta:
        verbose_name = "Data Disclosure Agreement Record History"
        verbose_name_plural = "Data Disclosure Agreement Record History"

    # Possible states (same as parent record)
    STATE_CHOICES = [
        ("unsigned", "unsigned"),  # Agreement was not signed at this point
        ("signed", "signed"),  # Agreement was signed at this point
    ]

    # Unique identifier for this history record
    id: models.UUIDField[UUID, UUID] = models.UUIDField(
        primary_key=True, default=uuid4, editable=False
    )

    # Signature state at this point in history
    state: models.CharField[str, str] = models.CharField(
        max_length=255, choices=STATE_CHOICES, default="unsigned"
    )

    # Reference to the subscribing organisation
    organisationId: models.ForeignKey[Organisation, Organisation] = models.ForeignKey(
        Organisation, on_delete=models.CASCADE
    )

    # Complete JSON snapshot of the DDA at this historical point
    # Preserves the exact agreement terms for audit purposes
    dataDisclosureAgreementRecord: JSONField[Any, Any] = JSONField()

    # Foreign key reference to the DDA template
    # Enables efficient queries across all records for a template
    dataDisclosureAgreementTemplate: models.ForeignKey[
        DataDisclosureAgreementTemplate, DataDisclosureAgreementTemplate
    ] = models.ForeignKey(
        DataDisclosureAgreementTemplate, max_length=255, on_delete=models.CASCADE
    )

    # String reference to the template ID
    # Provides redundancy for queries and external references
    dataDisclosureAgreementTemplateId: models.CharField[str, str] = models.CharField(
        max_length=255, null=False
    )

    # Reference to the specific template revision at this historical point
    dataDisclosureAgreementTemplateRevisionId: models.CharField[str, str] = (
        models.CharField(max_length=255, null=False)
    )

    # External identifier for this subscription
    # Correlates with DataDisclosureAgreementRecord.dataDisclosureAgreementRecordId
    dataDisclosureAgreementRecordId: models.CharField[str, str] = models.CharField(
        max_length=255
    )

    # Opt-in status at this historical point
    # Records whether consent was active at this time
    optIn: models.BooleanField[bool, bool] = models.BooleanField(default=False)

    # Timestamp when this history record was created
    # Represents the point in time being recorded
    createdAt: models.DateTimeField[datetime, datetime] = models.DateTimeField(
        auto_now_add=True
    )

    # Timestamp of any modifications to this history record
    # Generally should not change after creation (immutable audit record)
    updatedAt: models.DateTimeField[datetime, datetime] = models.DateTimeField(
        auto_now=True
    )

    def __str__(self) -> str:
        return str(self.id)
