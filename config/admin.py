from django.contrib import admin
from .models import DataSource,Verification, VerificationTemplate, ImageModel
from customadminsite.admin import myadminsite

# Register your models here.
admin.site.register(ImageModel)