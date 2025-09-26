from django.contrib import admin
from .models import DataDisclosureAgreement, DataDisclosureAgreementTemplate
from customadminsite.admin import myadminsite


class DataDisclosureAgreementAdmin(admin.ModelAdmin):
    list_display = ('templateId', 'purpose', 'status', 'createdAt', 'isLatestVersion')

    def get_list_display(self, request):
        return self.list_display


# myadminsite.register(DataDisclosureAgreement, DataDisclosureAgreementAdmin)
myadminsite.register(DataDisclosureAgreementTemplate, DataDisclosureAgreementAdmin)
