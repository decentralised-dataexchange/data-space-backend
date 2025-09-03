from uuid import uuid4
from django.db import models
from onboard.models import DataspaceUser
from jsonfield.fields import JSONField

# Create your models here.
class Organisation(models.Model):
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
    owsBaseUrl = models.CharField(max_length=255, null=True, blank=True)
    openApiUrl = models.CharField(max_length=255,null=True, blank=True)
    createdAt = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
    
class OrganisationIdentity(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    organisationId = models.ForeignKey(Organisation, on_delete=models.CASCADE)
    presentationExchangeId = models.CharField(max_length=50, unique=True)
    presentationState = models.CharField(max_length=50)
    isPresentationVerified = models.BooleanField(default=False)
    presentationRecord = JSONField()
    createdAt = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.id)
    
class OrganisationIdentityTemplate(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    organisationIdentityTemplateName = models.CharField(
        max_length=255, null=True, blank=True)
    issuerName = models.CharField(max_length=255, null=True, blank=True)
    issuerLocation = models.CharField(max_length=255, null=True, blank=True)
    issuerLogoUrl = models.CharField(max_length=255, null=True, blank=True)
    presentationDefinitionId = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return self.organisationIdentityTemplateName
