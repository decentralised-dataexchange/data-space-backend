from django.db import models
from uuid import uuid4
from config.models import DataSource

# Create your models here.
from django.db import models

class Connection(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    connectionId = models.CharField(max_length=256, db_index=True, unique=True)
    state = models.CharField(max_length=20)
    myDid = models.CharField(max_length=50)
    theirLabel = models.CharField(max_length=255)
    routingState = models.CharField(max_length=20)
    invitationKey = models.CharField(max_length=255)
    invitationMode = models.CharField(max_length=20)
    initiator = models.CharField(max_length=20)
    updatedAt = models.DateTimeField()
    accept = models.CharField(max_length=20)
    requestId = models.CharField(max_length=255)
    createdAt = models.DateTimeField()
    alias = models.CharField(max_length=255,null=True, blank=True)
    errorMsg = models.TextField(null=True, blank=True)
    inboundConnectionId = models.CharField(max_length=50,default=None,null=True, blank=True)
    theirDid = models.CharField(max_length=50,null=True, blank=True)
    theirRole = models.CharField(max_length=20,null=True, blank=True)
    dataSourceId = models.ForeignKey(DataSource, on_delete=models.CASCADE)

    def __str__(self):
        return self.connectionId