from django import forms
from django.contrib import admin

from organisation.models import (
    CodeOfConduct,
    Organisation,
    OrganisationIdentity,
    OrganisationIdentityTemplate,
    Sector,
)


class CodeOfConductAdminForm(forms.ModelForm):
    pdfFile = forms.FileField(
        required=False,
        label="PDF File",
        help_text="Upload a PDF file. It will be stored in the database.",
    )

    class Meta:
        model = CodeOfConduct
        fields = ["pdfFile", "isActive"]

    def save(self, commit=True):
        instance = super().save(commit=False)
        pdf_file = self.cleaned_data.get("pdfFile")
        if pdf_file:
            instance.pdfContent = pdf_file.read()
            instance.pdfFileName = pdf_file.name
        if commit:
            instance.save()
        return instance


class CodeOfConductAdmin(admin.ModelAdmin):
    form = CodeOfConductAdminForm
    list_display = ["id", "pdfFileName", "isActive", "createdAt", "updatedAt"]
    list_filter = ["isActive"]
    readonly_fields = ["id", "createdAt", "updatedAt", "pdfFileName"]

    def get_fields(self, request, obj=None):
        if obj:
            return ["id", "pdfFile", "pdfFileName", "isActive", "createdAt", "updatedAt"]
        return ["pdfFile", "isActive"]


# Register your models here.
admin.site.register(Organisation)
admin.site.register(OrganisationIdentity)
admin.site.register(OrganisationIdentityTemplate)
admin.site.register(Sector)
admin.site.register(CodeOfConduct, CodeOfConductAdmin)
