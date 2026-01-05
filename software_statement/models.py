from uuid import uuid4

from django.db import models
from jsonfield.fields import JSONField

from organisation.models import Organisation


# Create your models here.
class SoftwareStatement(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    organisationId = models.ForeignKey(Organisation, on_delete=models.CASCADE)
    credentialExchangeId = models.CharField(max_length=50, unique=True)
    status = models.CharField(max_length=50)
    credentialHistory = JSONField()
    createdAt = models.DateTimeField(auto_now_add=True)
    updatedAt = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.id)


class SoftwareStatementTemplate(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    softwareStatementTemplateName = models.CharField(
        max_length=255, null=True, blank=True
    )
    credentialDefinitionId = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return self.softwareStatementTemplateName
