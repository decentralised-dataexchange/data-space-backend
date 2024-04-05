from django.contrib import admin
from .models import DataSource,Verification, VerificationTemplate, ImageModel

# Register your models here.
admin.site.register(DataSource)
admin.site.register(Verification)
admin.site.register(VerificationTemplate)
admin.site.register(ImageModel)