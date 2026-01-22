from typing import Callable

from django.contrib import admin
from django.http import HttpRequest

from customadminsite.admin import myadminsite

from .models import DataDisclosureAgreementTemplate


class DataDisclosureAgreementAdmin(admin.ModelAdmin[DataDisclosureAgreementTemplate]):
    list_display = ("templateId", "purpose", "status", "createdAt", "isLatestVersion")

    def get_list_display(
        self, request: HttpRequest
    ) -> tuple[str | Callable[[DataDisclosureAgreementTemplate], str | bool], ...]:
        return self.list_display


# myadminsite.register(DataDisclosureAgreement, DataDisclosureAgreementAdmin)
myadminsite.register(DataDisclosureAgreementTemplate, DataDisclosureAgreementAdmin)
