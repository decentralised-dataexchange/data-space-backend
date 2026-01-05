from django.contrib import admin

from software_statement.models import SoftwareStatement, SoftwareStatementTemplate

# Register your models here.
admin.site.register(SoftwareStatement)
admin.site.register(SoftwareStatementTemplate)
