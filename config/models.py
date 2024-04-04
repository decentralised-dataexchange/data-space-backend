from django.db import models
from onboard.models import DataspaceUser
from uuid import uuid4
from jsonfield.fields import JSONField

# Create your models here.


class ImageModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    image_data = models.BinaryField()

    def __str__(self):
        return str(self.id)


class DataSource(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    coverImageUrl = models.CharField(max_length=255)
    logoUrl = models.CharField(max_length=255)
    name = models.CharField(max_length=100)
    sector = models.CharField(max_length=100)
    location = models.CharField(max_length=100)
    policyUrl = models.CharField(max_length=255)
    description = models.TextField()
    coverImageId = models.UUIDField(default=None, null=True, blank=True)
    logoId = models.UUIDField(default=None, null=True, blank=True)
    admin = models.OneToOneField(DataspaceUser, on_delete=models.CASCADE)
    openApiUrl = models.CharField(max_length=255,null=True, blank=True)

    def __str__(self):
        return self.name


class Verification(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    dataSourceId = models.ForeignKey(DataSource, on_delete=models.CASCADE)
    presentationExchangeId = models.CharField(max_length=50, unique=True)
    presentationState = models.CharField(max_length=50)
    presentationRecord = JSONField()

    def __str__(self):
        return str(self.id)



class VerificationTemplate(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    verificationTemplateName = models.CharField(
        max_length=255, null=True, blank=True)
    walletName = models.CharField(max_length=255, null=True, blank=True)
    walletLocation = models.CharField(max_length=255, null=True, blank=True)
    issuerName = models.CharField(max_length=255, null=True, blank=True)
    issuerLocation = models.CharField(max_length=255, null=True, blank=True)
    issuerLogoUrl = models.CharField(max_length=255, null=True, blank=True)
    dataSourceId = models.ForeignKey(DataSource, on_delete=models.CASCADE)
    dataAgreementId = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return self.verificationTemplateName
