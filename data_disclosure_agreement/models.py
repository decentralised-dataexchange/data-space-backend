"""
Data Disclosure Agreement Models Module

This module defines the core data sharing contract models for the data space platform.
Data Disclosure Agreements (DDAs) are legally-binding contracts that govern how data
is shared between organisations. They specify the purpose of data usage, data attributes
being shared, lawful basis, and other compliance requirements.

DDAs are central to the data space's trust framework, ensuring that all data exchange
activities are transparent, compliant, and governed by mutual consent.
"""

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from django.db import models
from django.db.models import QuerySet
from jsonfield.fields import JSONField

from config.models import DataSource
from organisation.models import Organisation


class DataDisclosureAgreement(models.Model):
    """
    Represents a versioned Data Disclosure Agreement for a data source.

    A Data Disclosure Agreement (DDA) is a standardized contract that defines
    the terms under which data is shared between a data provider (data source)
    and data consumers. This model stores both the metadata and the full JSON
    representation of the agreement.

    DDAs follow a lifecycle of states:
    - unlisted: Draft state, not visible to consumers
    - awaitingForApproval: Submitted for review by data space administrators
    - approved: Approved by administrators but not yet published
    - listed: Published and available for consumers to subscribe
    - rejected: Rejected by administrators

    Relationships:
        - Many-to-One with DataSource: Each DDA belongs to one data source
        - Versioning: Multiple DDAs can share a templateId but have different versions

    Business Rules:
        - Only one version of a DDA should have isLatestVersion=True per templateId
        - Listed DDAs are visible in the marketplace
        - Version history is preserved for audit and compliance

    Note: This model is associated with DataSource. For Organisation-based DDAs,
    see DataDisclosureAgreementTemplate.
    """

    class Meta:
        verbose_name = "Data Disclosure Agreement - Manage Listing"
        verbose_name_plural = "Data Disclosure Agreement - Manage Listing"

    # Available status values for the DDA lifecycle
    STATUS_CHOICES = [
        ("listed", "listed"),  # Published and available for subscription
        ("unlisted", "unlisted"),  # Draft or unpublished
        ("awaitingForApproval", "awaitingForApproval"),  # Pending admin review
        ("approved", "approved"),  # Approved but not yet published
        ("rejected", "rejected"),  # Rejected by administrator
    ]

    # Unique identifier for this DDA record
    id: models.UUIDField[UUID, UUID] = models.UUIDField(
        primary_key=True, default=uuid4, editable=False
    )

    # Semantic version number of this agreement (e.g., "1.0.0", "1.1.0")
    # Used to track changes and enable version comparison
    version: models.CharField[str, str] = models.CharField(max_length=255)

    # Identifier that groups all versions of the same agreement template
    # Multiple DDA records with the same templateId represent version history
    templateId: models.CharField[str, str] = models.CharField(max_length=255)

    # Current lifecycle status of the DDA
    # Determines visibility and availability in the marketplace
    status: models.CharField[str, str] = models.CharField(
        max_length=255, choices=STATUS_CHOICES, default="unlisted"
    )

    # Reference to the data source that owns this DDA
    # The data source is the data provider offering data under this agreement
    dataSourceId: models.ForeignKey[DataSource, DataSource] = models.ForeignKey(
        DataSource, on_delete=models.CASCADE
    )

    # Complete JSON representation of the Data Disclosure Agreement
    # Contains all agreement details: purpose, data attributes, lawful basis,
    # data controller info, third-party sharing details, retention period, etc.
    dataDisclosureAgreementRecord: JSONField[Any, Any] = JSONField()

    # Timestamp when this DDA version was created
    createdAt: models.DateTimeField[datetime, datetime] = models.DateTimeField(
        auto_now_add=True
    )

    # Flag indicating if this is the most recent version for this templateId
    # Used to quickly identify the current active version
    isLatestVersion: models.BooleanField[bool, bool] = models.BooleanField(default=True)

    @property
    def purpose(self) -> str:
        """
        Extract the purpose field from the DDA JSON record.

        The purpose describes why data is being collected/shared and is a
        key compliance element required by data protection regulations.
        """
        return f"{self.dataDisclosureAgreementRecord.get('purpose', None)}"

    @staticmethod
    def list_by_data_source_id(
        data_source_id: str, **kwargs: Any
    ) -> QuerySet["DataDisclosureAgreement"]:
        """
        Retrieve all DDAs for a specific data source, ordered by creation date.

        Args:
            data_source_id: UUID of the data source
            **kwargs: Additional filter parameters (e.g., status, templateId)

        Returns:
            QuerySet of DDAs matching the criteria, newest first
        """
        ddas: QuerySet[DataDisclosureAgreement] = (
            DataDisclosureAgreement.objects.filter(
                dataSourceId__id=data_source_id, **kwargs
            ).order_by("-createdAt")
        )
        return ddas

    @staticmethod
    def read_latest_dda_by_template_id_and_data_source_id(
        template_id: str, data_source_id: str
    ) -> "DataDisclosureAgreement | None":
        """
        Get the latest listed DDA for a specific template and data source.

        Used when consumers want to subscribe to a DDA - returns the current
        published version.

        Args:
            template_id: The template identifier grouping DDA versions
            data_source_id: UUID of the data source

        Returns:
            The latest listed DDA or None if not found
        """
        ddas = DataDisclosureAgreement.list_by_data_source_id(
            status="listed", templateId=template_id, data_source_id=data_source_id
        )
        if len(ddas) > 0:
            return ddas[0]
        else:
            return None

    @staticmethod
    def list_unique_dda_template_ids() -> list[str]:
        """
        Get all unique template IDs across all DDAs in the system.

        Useful for administrative dashboards and analytics.

        Returns:
            List of unique template ID strings
        """
        unique: list[str] = []
        ddas = DataDisclosureAgreement.objects.all()
        for dda in ddas:
            unique.append(str(dda.templateId))
        return list(set(unique))

    @staticmethod
    def list_unique_dda_template_ids_for_a_data_source(
        data_source_id: str, **kwargs: Any
    ) -> list[str]:
        """
        Get unique template IDs for a specific data source.

        Preserves the order of insertion based on creation date, allowing
        UIs to display templates in a consistent order.

        Args:
            data_source_id: UUID of the data source
            **kwargs: Additional filter parameters

        Returns:
            Ordered list of unique template IDs for the data source
        """
        unique_set: set[str] = set()
        ddas = DataDisclosureAgreement.list_by_data_source_id(
            data_source_id=data_source_id, **kwargs
        )
        for dda in ddas:
            unique_set.add(str(dda.templateId))

        # Convert set to list while preserving the order of insertion
        unique_list: list[str] = []
        for item in ddas:
            if str(item.templateId) in unique_set:
                unique_list.append(str(item.templateId))
                unique_set.remove(str(item.templateId))

        return unique_list

    def __str__(self) -> str:
        return str(self.id)


class DataDisclosureAgreementTemplate(models.Model):
    """
    Represents a versioned Data Disclosure Agreement Template for an organisation.

    This model is similar to DataDisclosureAgreement but is associated with
    Organisation instead of DataSource. It represents the modern, organisation-centric
    approach to managing DDAs in the data space.

    DDA Templates go through a lifecycle of review and approval before becoming
    available for data consumers to subscribe to. The template includes both
    the agreement content and revision tracking for compliance purposes.

    Relationships:
        - Many-to-One with Organisation: Each template belongs to one organisation
        - One-to-Many with DataDisclosureAgreementRecordHistory: Templates are referenced by records

    Business Rules:
        - Only one version should have isLatestVersion=True per templateId
        - Archived templates are excluded from listings but preserved for audit
        - Tags enable categorization and search functionality
    """

    class Meta:
        verbose_name = "Data Disclosure Agreement - Manage Listing"
        verbose_name_plural = "Data Disclosure Agreement - Manage Listing"

    # Available status values for the DDA template lifecycle
    STATUS_CHOICES = [
        ("listed", "listed"),  # Published and available for subscription
        ("unlisted", "unlisted"),  # Draft or unpublished
        ("awaitingForApproval", "awaitingForApproval"),  # Pending admin review
        ("approved", "approved"),  # Approved but not yet published
        ("rejected", "rejected"),  # Rejected by administrator
        ("archived", "archived"),  # Soft-deleted, preserved for history
    ]

    # Unique identifier for this DDA template record
    id: models.UUIDField[UUID, UUID] = models.UUIDField(
        primary_key=True, default=uuid4, editable=False
    )

    # Semantic version number (e.g., "1.0.0", "2.0.0")
    # Incremented when agreement terms change
    version: models.CharField[str, str] = models.CharField(max_length=255)

    # Identifier grouping all versions of the same agreement template
    # Enables version history and upgrade paths
    templateId: models.CharField[str, str] = models.CharField(max_length=255)

    # Current lifecycle status of the DDA template
    status: models.CharField[str, str] = models.CharField(
        max_length=255, choices=STATUS_CHOICES, default="unlisted"
    )

    # Reference to the organisation that owns this DDA template
    # The organisation is the data provider
    organisationId: models.ForeignKey[Organisation, Organisation] = models.ForeignKey(
        Organisation, on_delete=models.CASCADE
    )

    # Complete JSON representation of the Data Disclosure Agreement
    # Contains purpose, data attributes, lawful basis, third-party sharing, etc.
    dataDisclosureAgreementRecord: JSONField[Any, Any] = JSONField()

    # JSON record of the template revision for change tracking
    # Captures the state of the template at each version
    dataDisclosureAgreementTemplateRevision: JSONField[Any, Any] = JSONField()

    # Unique identifier for this specific revision
    # Used to reference exact versions in records and audit trails
    dataDisclosureAgreementTemplateRevisionId: models.CharField[
        str | None, str | None
    ] = models.CharField(max_length=255, null=True)

    # Timestamp when this DDA template version was created
    createdAt: models.DateTimeField[datetime, datetime] = models.DateTimeField(
        auto_now_add=True
    )

    # Flag indicating if this is the most recent version for this templateId
    isLatestVersion: models.BooleanField[bool, bool] = models.BooleanField(default=True)

    # Timestamp when this DDA template was last modified
    updatedAt: models.DateTimeField[datetime, datetime] = models.DateTimeField(
        auto_now=True
    )

    # Categorization tags for search and filtering
    # Enables discovery by industry, data type, or use case
    # Example: ["healthcare", "personal-data", "research"]
    tags: JSONField[Any, Any] = JSONField(
        default=list, blank=True
    )  # e.g., ["healthcare", "finance"]

    @property
    def purpose(self) -> str:
        """
        Extract the purpose field from the DDA JSON record.

        The purpose is a key compliance element describing why data is shared.
        """
        return f"{self.dataDisclosureAgreementRecord.get('purpose', None)}"

    @staticmethod
    def list_by_data_source_id(
        data_source_id: str, **kwargs: Any
    ) -> QuerySet["DataDisclosureAgreementTemplate"]:
        """
        Retrieve all DDA templates for a specific organisation, excluding archived.

        Note: Despite the name 'data_source_id', this filters by organisationId
        for backward compatibility.

        Args:
            data_source_id: UUID of the organisation
            **kwargs: Additional filter parameters

        Returns:
            QuerySet of DDA templates, newest first, excluding archived
        """
        ddas: QuerySet[DataDisclosureAgreementTemplate] = (
            DataDisclosureAgreementTemplate.objects.filter(
                organisationId__id=data_source_id, **kwargs
            )
            .exclude(status="archived")
            .order_by("-createdAt")
        )
        return ddas

    @staticmethod
    def read_latest_dda_by_template_id_and_data_source_id(
        template_id: str, data_source_id: str
    ) -> "DataDisclosureAgreementTemplate | None":
        """
        Get the latest listed DDA template for a specific template and organisation.

        Args:
            template_id: The template identifier
            data_source_id: UUID of the organisation

        Returns:
            The latest listed template or None
        """
        ddas = DataDisclosureAgreementTemplate.list_by_data_source_id(
            status="listed", templateId=template_id, data_source_id=data_source_id
        )
        if len(ddas) > 0:
            return ddas[0]
        else:
            return None

    @staticmethod
    def list_unique_dda_template_ids() -> list[str]:
        """
        Get all unique template IDs across all DDA templates.

        Returns:
            List of unique template ID strings
        """
        unique: list[str] = []
        ddas = DataDisclosureAgreementTemplate.objects.all()
        for dda in ddas:
            unique.append(str(dda.templateId))
        return list(set(unique))

    @staticmethod
    def list_unique_dda_template_ids_for_a_data_source(
        data_source_id: str, **kwargs: Any
    ) -> list[str]:
        """
        Get unique template IDs for a specific organisation.

        Preserves insertion order based on creation date.

        Args:
            data_source_id: UUID of the organisation
            **kwargs: Additional filter parameters

        Returns:
            Ordered list of unique template IDs
        """
        unique_set: set[str] = set()
        ddas = DataDisclosureAgreementTemplate.list_by_data_source_id(
            data_source_id=data_source_id, **kwargs
        )
        for dda in ddas:
            unique_set.add(str(dda.templateId))

        # Convert set to list while preserving the order of insertion
        unique_list: list[str] = []
        for item in ddas:
            if str(item.templateId) in unique_set:
                unique_list.append(str(item.templateId))
                unique_set.remove(str(item.templateId))

        return unique_list

    def __str__(self) -> str:
        return str(self.id)
