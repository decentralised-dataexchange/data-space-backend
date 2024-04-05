import typing
from django.db import models
from uuid import uuid4
from jsonfield.fields import JSONField
from config.models import DataSource
from time import time


# Create your models here.
class DataDisclosureAgreement(models.Model):

    STATUS_CHOICES = [
        ("listed", "listed"),
        ("unlisted", "unlisted"),
        ("awaitingForApproval", "awaitingForApproval"),
        ("approved", "approved"),
        ("rejected", "rejected"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    version = models.CharField(max_length=255)
    templateId = models.CharField(max_length=255)
    status = models.CharField(
        max_length=255, choices=STATUS_CHOICES, default="unlisted"
    )
    dataSourceId = models.ForeignKey(DataSource, on_delete=models.CASCADE)
    dataDisclosureAgreementRecord = JSONField()
    createdAt = models.DateTimeField(auto_now_add=True)
    isLatestVersion = models.BooleanField(default=True)

    @staticmethod
    def list_by_data_source_id(
        data_source_id: str, **kwargs
    ) -> typing.List["DataDisclosureAgreement"]:
        ddas = DataDisclosureAgreement.objects.filter(
            dataSourceId__id=data_source_id, **kwargs
        ).order_by("-createdAt")
        return ddas

    @staticmethod
    def read_latest_dda_by_template_id_and_data_source_id(template_id: str, data_source_id: str) -> "DataDisclosureAgreement":
        ddas = DataDisclosureAgreement.list_by_data_source_id(status="listed", templateId=template_id, data_source_id=data_source_id)
        if (len(ddas) > 0):
            return ddas[0]
        else:
            return None
    
    @staticmethod
    def list_unique_dda_template_ids() -> typing.List[str]:
        unique = []
        ddas = DataDisclosureAgreement.objects.all()
        for dda in ddas:
            unique.append(dda.templateId)
        return list(set(unique))
    
    @staticmethod
    def list_unique_dda_template_ids_for_a_data_source(data_source_id,**kwargs) -> typing.List[str]:
        unique = []
        ddas = DataDisclosureAgreement.list_by_data_source_id(data_source_id=data_source_id,**kwargs)
        for dda in ddas:
            unique.append(dda.templateId)
        return list(set(unique))

    def __str__(self):
        return str(self.id)
