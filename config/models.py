from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from django.db import models
from jsonfield.fields import JSONField

from onboard.models import DataspaceUser

# Create your models here.


class ImageModel(models.Model):
    id: models.UUIDField[UUID, UUID] = models.UUIDField(
        primary_key=True, default=uuid4, editable=False
    )
    image_data: models.BinaryField[bytes, bytes] = models.BinaryField()

    def __str__(self) -> str:
        return str(self.id)


class DataSource(models.Model):
    id: models.UUIDField[UUID, UUID] = models.UUIDField(
        primary_key=True, default=uuid4, editable=False
    )
    coverImageUrl: models.CharField[str, str] = models.CharField(max_length=255)
    logoUrl: models.CharField[str, str] = models.CharField(max_length=255)
    name: models.CharField[str, str] = models.CharField(max_length=100)
    sector: models.CharField[str, str] = models.CharField(max_length=100)
    location: models.CharField[str, str] = models.CharField(max_length=100)
    policyUrl: models.CharField[str, str] = models.CharField(max_length=255)
    description: models.TextField[str, str] = models.TextField()
    coverImageId: models.UUIDField[UUID | None, UUID | None] = models.UUIDField(
        default=None, null=True, blank=True
    )
    logoId: models.UUIDField[UUID | None, UUID | None] = models.UUIDField(
        default=None, null=True, blank=True
    )
    admin: models.OneToOneField[DataspaceUser, DataspaceUser] = models.OneToOneField(
        DataspaceUser, on_delete=models.CASCADE
    )
    openApiUrl: models.CharField[str | None, str | None] = models.CharField(
        max_length=255, null=True, blank=True
    )
    createdAt: models.DateTimeField[datetime, datetime] = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self) -> str:
        return str(self.name)


class Verification(models.Model):
    id: models.UUIDField[UUID, UUID] = models.UUIDField(
        primary_key=True, default=uuid4, editable=False
    )
    dataSourceId: models.ForeignKey[DataSource, DataSource] = models.ForeignKey(
        DataSource, on_delete=models.CASCADE
    )
    presentationExchangeId: models.CharField[str, str] = models.CharField(
        max_length=50, unique=True
    )
    presentationState: models.CharField[str, str] = models.CharField(max_length=50)
    presentationRecord: JSONField[Any, Any] = JSONField()

    def __str__(self) -> str:
        return str(self.id)


class VerificationTemplate(models.Model):
    id: models.UUIDField[UUID, UUID] = models.UUIDField(
        primary_key=True, default=uuid4, editable=False
    )
    verificationTemplateName: models.CharField[str | None, str | None] = (
        models.CharField(max_length=255, null=True, blank=True)
    )
    issuerName: models.CharField[str | None, str | None] = models.CharField(
        max_length=255, null=True, blank=True
    )
    issuerLocation: models.CharField[str | None, str | None] = models.CharField(
        max_length=255, null=True, blank=True
    )
    issuerLogoUrl: models.CharField[str | None, str | None] = models.CharField(
        max_length=255, null=True, blank=True
    )
    dataAgreementId: models.CharField[str | None, str | None] = models.CharField(
        max_length=255, null=True, blank=True
    )

    def __str__(self) -> str:
        return str(self.verificationTemplateName)
