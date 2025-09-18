from uuid import uuid4
from django.db import models
from jsonfield.fields import JSONField
from organisation.models import Organisation
from data_disclosure_agreement.models import DataDisclosureAgreementTemplate


# Create your models here.
class DataDisclosureAgreementRecord(models.Model):

    class Meta:
        verbose_name = "Data Disclosure Agreement Record"
        verbose_name_plural = "Data Disclosure Agreement Record"

    STATE_CHOICES = [
        ("unsigned", "unsigned"),
        ("signed", "signed"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    state = models.CharField(
        max_length=255, choices=STATE_CHOICES, default="unsigned"
    )
    organisationId = models.ForeignKey(Organisation, on_delete=models.CASCADE)
    dataDisclosureAgreementRecord = JSONField()
    dataDisclosureAgreementTemplateId = models.CharField(max_length=255, null=False)
    dataDisclosureAgreementTemplateRevisionId = models.CharField(max_length=255, null=False)
    dataDisclosureAgreementRecordId = models.CharField(max_length=255, null=False)
    optIn = models.BooleanField(default=False)
    createdAt = models.DateTimeField(auto_now_add=True)
    updatedAt = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.id)


class DataDisclosureAgreementRecordHistory(models.Model):

    class Meta:
        verbose_name = "Data Disclosure Agreement Record History"
        verbose_name_plural = "Data Disclosure Agreement Record History"

    STATE_CHOICES = [
        ("unsigned", "unsigned"),
        ("signed", "signed"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    state = models.CharField(
        max_length=255, choices=STATE_CHOICES, default="unsigned"
    )
    organisationId = models.ForeignKey(Organisation, on_delete=models.CASCADE)
    dataDisclosureAgreementRecord = JSONField()
    dataDisclosureAgreementTemplate = models.ForeignKey(DataDisclosureAgreementTemplate,max_length=255, on_delete=models.CASCADE)
    dataDisclosureAgreementTemplateId = models.CharField(max_length=255,null=False)
    dataDisclosureAgreementTemplateRevisionId = models.CharField(max_length=255,null=False)
    dataDisclosureAgreementRecordId = models.CharField(max_length=255)
    optIn = models.BooleanField(default=False)
    createdAt = models.DateTimeField(auto_now_add=True)
    updatedAt = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.id)