from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from django.db import models
from jsonfield.fields import JSONField

from organisation.models import Organisation


# Create your models here.
class SoftwareStatement(models.Model):
    id: models.UUIDField[UUID, UUID] = models.UUIDField(
        primary_key=True, default=uuid4, editable=False
    )
    organisationId: models.ForeignKey[Organisation, Organisation] = models.ForeignKey(
        Organisation, on_delete=models.CASCADE
    )
    credentialExchangeId: models.CharField[str, str] = models.CharField(
        max_length=50, unique=True
    )
    status: models.CharField[str, str] = models.CharField(max_length=50)
    credentialHistory: JSONField[Any, Any] = JSONField()
    createdAt: models.DateTimeField[datetime, datetime] = models.DateTimeField(
        auto_now_add=True
    )
    updatedAt: models.DateTimeField[datetime, datetime] = models.DateTimeField(
        auto_now=True
    )

    def __str__(self) -> str:
        return str(self.id)


class SoftwareStatementTemplate(models.Model):
    id: models.UUIDField[UUID, UUID] = models.UUIDField(
        primary_key=True, default=uuid4, editable=False
    )
    softwareStatementTemplateName: models.CharField[str | None, str | None] = (
        models.CharField(max_length=255, null=True, blank=True)
    )
    credentialDefinitionId: models.CharField[str | None, str | None] = models.CharField(
        max_length=255, null=True, blank=True
    )

    def __str__(self) -> str:
        return str(self.softwareStatementTemplateName)
