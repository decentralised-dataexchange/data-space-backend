from django.contrib import admin
from .models import DataDisclosureAgreement
from customadminsite.admin import myadminsite


class DataDisclosureAgreementAdmin(admin.ModelAdmin):
    list_display = ('templateId', 'status', 'createdAt', 'isLatestVersion')

    def get_list_display(self, request):
        return self.list_display


myadminsite.register(DataDisclosureAgreement, DataDisclosureAgreementAdmin)
