from uuid import uuid4

from django.db import models
from jsonfield.fields import JSONField

from config.models import DataSource

# Create your models here.


class Connection(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    connectionId = models.CharField(max_length=256, db_index=True, unique=True)
    connectionState = models.CharField(max_length=20)
    dataSourceId = models.ForeignKey(DataSource, on_delete=models.CASCADE)
    connectionRecord = JSONField(max_length=512)

    def __str__(self):
        return self.connectionId
