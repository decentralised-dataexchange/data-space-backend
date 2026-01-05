from uuid import uuid4

from django.db import models
from jsonfield.fields import JSONField

from organisation.models import Organisation

# Create your models here.


class B2BConnection(models.Model):
    class Meta:
        verbose_name = "B2B Connection"
        verbose_name_plural = "B2B Connection"

    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    organisationId = models.ForeignKey(Organisation, on_delete=models.CASCADE)
    b2bConnectionRecord = JSONField()
    b2bConnectionId = models.CharField(max_length=255, null=False)
    createdAt = models.DateTimeField(auto_now_add=True)
    updatedAt = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.id)
