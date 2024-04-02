from django.db import models
from uuid import uuid4
from jsonfield.fields import JSONField
from config.models import DataSource

# Create your models here.
class DataDisclosureAgreement(models.Model):

    STATUS_CHOICES = [
        ('listed', 'listed'),
        ('unlisted', 'unlisted'),
        ('awaitingForApproval', 'awaitingForApproval'),
        ('approved', 'approved'),
        ('rejected', 'rejected'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    language = models.CharField(max_length=255)
    version = models.CharField(max_length=255)
    templateId = models.CharField(max_length=255)
    templateVersion = models.CharField(max_length=255)
    dataController = JSONField()
    agreementPeriod = models.IntegerField()
    dataSharingRestrictions = JSONField()
    purpose = models.CharField(max_length=255)
    purposeDescription = models.CharField(max_length=255)
    lawfulBasis = models.CharField(max_length=255)
    personalData = JSONField(default=list, blank=True)
    codeOfConduct = models.CharField(max_length=255)
    status = models.CharField(max_length=255, choices=STATUS_CHOICES, default='awaitingForApproval')
    dataSourceId = models.ForeignKey(DataSource, on_delete=models.CASCADE)

    revisions = JSONField(default=list, blank=True)

    def __str__(self):
        return str(self.id)