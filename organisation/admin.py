from django.contrib import admin
from organisation.models import Organisation, OrganisationIdentity, OrganisationIdentityTemplate, Sector, CodeOfConduct

# Register your models here.
admin.site.register(Organisation)
admin.site.register(OrganisationIdentity)
admin.site.register(OrganisationIdentityTemplate)
admin.site.register(Sector)
admin.site.register(CodeOfConduct)