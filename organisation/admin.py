from django.contrib import admin

from organisation.models import (
    CodeOfConduct,
    Organisation,
    OrganisationIdentity,
    OrganisationIdentityTemplate,
    Sector,
)

# Register your models here.
admin.site.register(Organisation)
admin.site.register(OrganisationIdentity)
admin.site.register(OrganisationIdentityTemplate)
admin.site.register(Sector)
admin.site.register(CodeOfConduct)
