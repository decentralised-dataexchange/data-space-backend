from django.contrib import admin

from customadminsite.admin import myadminsite

from .models import DataDisclosureAgreementTemplate


class DataDisclosureAgreementAdmin(admin.ModelAdmin):
    list_display = ("templateId", "purpose", "status", "createdAt", "isLatestVersion")

    def get_list_display(self, request):
        return self.list_display


# myadminsite.register(DataDisclosureAgreement, DataDisclosureAgreementAdmin)
myadminsite.register(DataDisclosureAgreementTemplate, DataDisclosureAgreementAdmin)
