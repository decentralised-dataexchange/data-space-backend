from django.contrib import admin
from .models import DataDisclosureAgreement
from customadminsite.admin import myadminsite

# Register your models here.
myadminsite.register(DataDisclosureAgreement)