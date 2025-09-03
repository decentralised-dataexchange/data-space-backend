import typing
from django.db import models
from uuid import uuid4
from jsonfield.fields import JSONField
from config.models import DataSource
from time import time
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

    @property
    def purpose(self):
        return f"{self.dataDisclosureAgreementRecord.get('purpose', None)}"

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
    def list_unique_dda_template_ids_for_a_data_source(data_source_id, **kwargs) -> typing.List[str]:
        unique_set = set()
        ddas = DataDisclosureAgreement.list_by_data_source_id(data_source_id=data_source_id, **kwargs)
        for dda in ddas:
            unique_set.add(dda.templateId)
        
        # Convert set to list while preserving the order of insertion
        unique_list = []
        for item in ddas:
            if item.templateId in unique_set:
                unique_list.append(item.templateId)
                unique_set.remove(item.templateId)
        
        return unique_list

    def __str__(self):
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
    ]

    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    version = models.CharField(max_length=255)
    templateId = models.CharField(max_length=255)
    status = models.CharField(
        max_length=255, choices=STATUS_CHOICES, default="unlisted"
    )
    organisationId = models.ForeignKey(Organisation, on_delete=models.CASCADE)
    dataDisclosureAgreementRecord = JSONField()
    createdAt = models.DateTimeField(auto_now_add=True)
    isLatestVersion = models.BooleanField(default=True)

    @property
    def purpose(self):
        return f"{self.dataDisclosureAgreementRecord.get('purpose', None)}"

    @staticmethod
    def list_by_data_source_id(
        data_source_id: str, **kwargs
    ) -> typing.List["DataDisclosureAgreementTemplate"]:
        ddas = DataDisclosureAgreementTemplate.objects.filter(
            organisationId__id=data_source_id, **kwargs
        ).order_by("-createdAt")
        return ddas

    @staticmethod
    def read_latest_dda_by_template_id_and_data_source_id(template_id: str, data_source_id: str) -> "DataDisclosureAgreementTemplate":
        ddas = DataDisclosureAgreementTemplate.list_by_data_source_id(status="listed", templateId=template_id, data_source_id=data_source_id)
        if (len(ddas) > 0):
            return ddas[0]
        else:
            return None
    
    @staticmethod
    def list_unique_dda_template_ids() -> typing.List[str]:
        unique = []
        ddas = DataDisclosureAgreementTemplate.objects.all()
        for dda in ddas:
            unique.append(dda.templateId)
        return list(set(unique))
    
    @staticmethod
    def list_unique_dda_template_ids_for_a_data_source(data_source_id, **kwargs) -> typing.List[str]:
        unique_set = set()
        ddas = DataDisclosureAgreementTemplate.list_by_data_source_id(data_source_id=data_source_id, **kwargs)
        for dda in ddas:
            unique_set.add(dda.templateId)
        
        # Convert set to list while preserving the order of insertion
        unique_list = []
        for item in ddas:
            if item.templateId in unique_set:
                unique_list.append(item.templateId)
                unique_set.remove(item.templateId)
        
        return unique_list

    def __str__(self):
        return str(self.id)
