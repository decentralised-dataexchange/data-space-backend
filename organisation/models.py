from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from django.db import models
from jsonfield.fields import JSONField

from onboard.models import DataspaceUser


# Create your models here.
class Organisation(models.Model):
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
    owsBaseUrl: models.CharField[str | None, str | None] = models.CharField(
        max_length=255, null=True, blank=True
    )
    openApiUrl: models.CharField[str | None, str | None] = models.CharField(
        max_length=255, null=True, blank=True
    )
    credentialOfferEndpoint: models.CharField[str | None, str | None] = (
        models.CharField(max_length=255, null=True, blank=True)
    )
    accessPointEndpoint: models.CharField[str | None, str | None] = models.CharField(
        max_length=255, null=True, blank=True
    )
    codeOfConduct: models.BooleanField[bool, bool] = models.BooleanField(default=False)
    privacyDashboardUrl: models.CharField[str | None, str | None] = models.CharField(
        max_length=255, null=True, blank=True
    )
    createdAt: models.DateTimeField[datetime, datetime] = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self) -> str:
        return str(self.name)


class OrganisationIdentity(models.Model):
    id: models.UUIDField[UUID, UUID] = models.UUIDField(
        primary_key=True, default=uuid4, editable=False
    )
    organisationId: models.ForeignKey[Organisation, Organisation] = models.ForeignKey(
        Organisation, on_delete=models.CASCADE
    )
    presentationExchangeId: models.CharField[str, str] = models.CharField(
        max_length=50, unique=True
    )
    presentationState: models.CharField[str, str] = models.CharField(max_length=50)
    isPresentationVerified: models.BooleanField[bool, bool] = models.BooleanField(
        default=False
    )
    presentationRecord: JSONField[Any, Any] = JSONField()
    createdAt: models.DateTimeField[datetime, datetime] = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self) -> str:
        return str(self.id)

    class Meta:
        verbose_name = "Organisation Identity"
        verbose_name_plural = "Organisation Identities"


class OrganisationIdentityTemplate(models.Model):
    id: models.UUIDField[UUID, UUID] = models.UUIDField(
        primary_key=True, default=uuid4, editable=False
    )
    organisationIdentityTemplateName: models.CharField[str | None, str | None] = (
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
    presentationDefinitionId: models.CharField[str | None, str | None] = (
        models.CharField(max_length=255, null=True, blank=True)
    )

    def __str__(self) -> str:
        return str(self.organisationIdentityTemplateName)

    class Meta:
        verbose_name = "Organisation Identity Template"
        verbose_name_plural = "Organisation Identity Template"


class Sector(models.Model):
    id: models.UUIDField[UUID, UUID] = models.UUIDField(
        primary_key=True, default=uuid4, editable=False
    )
    sectorName: models.CharField[str, str] = models.CharField(
        max_length=100, unique=True
    )

    def __str__(self) -> str:
        return str(self.sectorName)

    class Meta:
        verbose_name = "Organisation Sector"
        verbose_name_plural = "Organisation Sectors"


class CodeOfConduct(models.Model):
    id: models.UUIDField[UUID, UUID] = models.UUIDField(
        primary_key=True, default=uuid4, editable=False
    )
    pdfContent: models.BinaryField[bytes | None, bytes | None] = models.BinaryField(
        null=True, blank=True
    )
    pdfFileName: models.CharField[str | None, str | None] = models.CharField(
        max_length=255, null=True, blank=True
    )
    createdAt: models.DateTimeField[datetime, datetime] = models.DateTimeField(
        auto_now_add=True
    )
    updatedAt: models.DateTimeField[datetime, datetime] = models.DateTimeField(
        auto_now=True
    )
    isActive: models.BooleanField[bool, bool] = models.BooleanField(default=True)

    def __str__(self) -> str:
        return f"Code of Conduct - {self.updatedAt.strftime('%Y-%m-%d %H:%M')}"

    class Meta:
        verbose_name = "Code of Conduct"
        verbose_name_plural = "Code of Conduct"
        ordering = ["-updatedAt"]
