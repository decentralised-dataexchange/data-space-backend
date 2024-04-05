from django.contrib import admin
from .models import DataSource,Verification, VerificationTemplate, ImageModel
from customadminsite.admin import myadminsite

# Register your models here.
admin.site.register(DataSource)
admin.site.register(Verification)
admin.site.register(VerificationTemplate)
admin.site.register(ImageModel)

myadminsite.register(DataSource)
myadminsite.register(Verification)
myadminsite.register(VerificationTemplate)
myadminsite.register(ImageModel)