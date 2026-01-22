from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from django.db import models
from django.db.models import QuerySet
from jsonfield.fields import JSONField

from config.models import DataSource
from organisation.models import Organisation


# Create your models here.
class DataDisclosureAgreement(models.Model):
    class Meta:
        verbose_name = "Data Disclosure Agreement - Manage Listing"
        verbose_name_plural = "Data Disclosure Agreement - Manage Listing"

    STATUS_CHOICES = [
        ("listed", "listed"),
        ("unlisted", "unlisted"),
        ("awaitingForApproval", "awaitingForApproval"),
        ("approved", "approved"),
        ("rejected", "rejected"),
    ]

    id: models.UUIDField[UUID, UUID] = models.UUIDField(
        primary_key=True, default=uuid4, editable=False
    )
    version: models.CharField[str, str] = models.CharField(max_length=255)
    templateId: models.CharField[str, str] = models.CharField(max_length=255)
    status: models.CharField[str, str] = models.CharField(
        max_length=255, choices=STATUS_CHOICES, default="unlisted"
    )
    dataSourceId: models.ForeignKey[DataSource, DataSource] = models.ForeignKey(
        DataSource, on_delete=models.CASCADE
    )
    dataDisclosureAgreementRecord: JSONField[Any, Any] = JSONField()
    createdAt: models.DateTimeField[datetime, datetime] = models.DateTimeField(
        auto_now_add=True
    )
    isLatestVersion: models.BooleanField[bool, bool] = models.BooleanField(default=True)

    @property
    def purpose(self) -> str:
        return f"{self.dataDisclosureAgreementRecord.get('purpose', None)}"

    @staticmethod
    def list_by_data_source_id(
        data_source_id: str, **kwargs: Any
    ) -> QuerySet["DataDisclosureAgreement"]:
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
        ddas = DataDisclosureAgreement.list_by_data_source_id(
            status="listed", templateId=template_id, data_source_id=data_source_id
        )
        if len(ddas) > 0:
            return ddas[0]
        else:
            return None

    @staticmethod
    def list_unique_dda_template_ids() -> list[str]:
        unique: list[str] = []
        ddas = DataDisclosureAgreement.objects.all()
        for dda in ddas:
            unique.append(str(dda.templateId))
        return list(set(unique))

    @staticmethod
    def list_unique_dda_template_ids_for_a_data_source(
        data_source_id: str, **kwargs: Any
    ) -> list[str]:
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
    class Meta:
        verbose_name = "Data Disclosure Agreement - Manage Listing"
        verbose_name_plural = "Data Disclosure Agreement - Manage Listing"

    STATUS_CHOICES = [
        ("listed", "listed"),
        ("unlisted", "unlisted"),
        ("awaitingForApproval", "awaitingForApproval"),
        ("approved", "approved"),
        ("rejected", "rejected"),
        ("archived", "archived"),
    ]

    id: models.UUIDField[UUID, UUID] = models.UUIDField(
        primary_key=True, default=uuid4, editable=False
    )
    version: models.CharField[str, str] = models.CharField(max_length=255)
    templateId: models.CharField[str, str] = models.CharField(max_length=255)
    status: models.CharField[str, str] = models.CharField(
        max_length=255, choices=STATUS_CHOICES, default="unlisted"
    )
    organisationId: models.ForeignKey[Organisation, Organisation] = models.ForeignKey(
        Organisation, on_delete=models.CASCADE
    )
    dataDisclosureAgreementRecord: JSONField[Any, Any] = JSONField()
    dataDisclosureAgreementTemplateRevision: JSONField[Any, Any] = JSONField()
    dataDisclosureAgreementTemplateRevisionId: models.CharField[
        str | None, str | None
    ] = models.CharField(max_length=255, null=True)
    createdAt: models.DateTimeField[datetime, datetime] = models.DateTimeField(
        auto_now_add=True
    )
    isLatestVersion: models.BooleanField[bool, bool] = models.BooleanField(default=True)
    updatedAt: models.DateTimeField[datetime, datetime] = models.DateTimeField(
        auto_now=True
    )
    tags: JSONField[Any, Any] = JSONField(
        default=list, blank=True
    )  # e.g., ["healthcare", "finance"]

    @property
    def purpose(self) -> str:
        return f"{self.dataDisclosureAgreementRecord.get('purpose', None)}"

    @staticmethod
    def list_by_data_source_id(
        data_source_id: str, **kwargs: Any
    ) -> QuerySet["DataDisclosureAgreementTemplate"]:
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
        ddas = DataDisclosureAgreementTemplate.list_by_data_source_id(
            status="listed", templateId=template_id, data_source_id=data_source_id
        )
        if len(ddas) > 0:
            return ddas[0]
        else:
            return None

    @staticmethod
    def list_unique_dda_template_ids() -> list[str]:
        unique: list[str] = []
        ddas = DataDisclosureAgreementTemplate.objects.all()
        for dda in ddas:
            unique.append(str(dda.templateId))
        return list(set(unique))

    @staticmethod
    def list_unique_dda_template_ids_for_a_data_source(
        data_source_id: str, **kwargs: Any
    ) -> list[str]:
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
