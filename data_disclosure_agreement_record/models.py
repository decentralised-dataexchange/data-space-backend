from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from django.db import models
from jsonfield.fields import JSONField

from data_disclosure_agreement.models import DataDisclosureAgreementTemplate
from organisation.models import Organisation


# Create your models here.
class DataDisclosureAgreementRecord(models.Model):
    class Meta:
        verbose_name = "Data Disclosure Agreement Record"
        verbose_name_plural = "Data Disclosure Agreement Record"

    STATE_CHOICES = [
        ("unsigned", "unsigned"),
        ("signed", "signed"),
    ]

    id: models.UUIDField[UUID, UUID] = models.UUIDField(
        primary_key=True, default=uuid4, editable=False
    )
    state: models.CharField[str, str] = models.CharField(
        max_length=255, choices=STATE_CHOICES, default="unsigned"
    )
    organisationId: models.ForeignKey[Organisation, Organisation] = models.ForeignKey(
        Organisation, on_delete=models.CASCADE
    )
    dataDisclosureAgreementRecord: JSONField[Any, Any] = JSONField()
    dataDisclosureAgreementTemplateId: models.CharField[str, str] = models.CharField(
        max_length=255, null=False
    )
    dataDisclosureAgreementTemplateRevisionId: models.CharField[str, str] = (
        models.CharField(max_length=255, null=False)
    )
    dataDisclosureAgreementRecordId: models.CharField[str, str] = models.CharField(
        max_length=255, null=False
    )
    optIn: models.BooleanField[bool, bool] = models.BooleanField(default=False)
    createdAt: models.DateTimeField[datetime, datetime] = models.DateTimeField(
        auto_now_add=True
    )
    updatedAt: models.DateTimeField[datetime, datetime] = models.DateTimeField(
        auto_now=True
    )

    def __str__(self) -> str:
        return str(self.id)


class DataDisclosureAgreementRecordHistory(models.Model):
    class Meta:
        verbose_name = "Data Disclosure Agreement Record History"
        verbose_name_plural = "Data Disclosure Agreement Record History"

    STATE_CHOICES = [
        ("unsigned", "unsigned"),
        ("signed", "signed"),
    ]

    id: models.UUIDField[UUID, UUID] = models.UUIDField(
        primary_key=True, default=uuid4, editable=False
    )
    state: models.CharField[str, str] = models.CharField(
        max_length=255, choices=STATE_CHOICES, default="unsigned"
    )
    organisationId: models.ForeignKey[Organisation, Organisation] = models.ForeignKey(
        Organisation, on_delete=models.CASCADE
    )
    dataDisclosureAgreementRecord: JSONField[Any, Any] = JSONField()
    dataDisclosureAgreementTemplate: models.ForeignKey[
        DataDisclosureAgreementTemplate, DataDisclosureAgreementTemplate
    ] = models.ForeignKey(
        DataDisclosureAgreementTemplate, max_length=255, on_delete=models.CASCADE
    )
    dataDisclosureAgreementTemplateId: models.CharField[str, str] = models.CharField(
        max_length=255, null=False
    )
    dataDisclosureAgreementTemplateRevisionId: models.CharField[str, str] = (
        models.CharField(max_length=255, null=False)
    )
    dataDisclosureAgreementRecordId: models.CharField[str, str] = models.CharField(
        max_length=255
    )
    optIn: models.BooleanField[bool, bool] = models.BooleanField(default=False)
    createdAt: models.DateTimeField[datetime, datetime] = models.DateTimeField(
        auto_now_add=True
    )
    updatedAt: models.DateTimeField[datetime, datetime] = models.DateTimeField(
        auto_now=True
    )

    def __str__(self) -> str:
        return str(self.id)
