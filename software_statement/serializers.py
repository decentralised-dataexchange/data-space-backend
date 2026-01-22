from rest_framework import serializers

from software_statement.models import SoftwareStatement, SoftwareStatementTemplate


class SoftwareStatementSerializer(serializers.ModelSerializer[SoftwareStatement]):
    class Meta:
        model = SoftwareStatement
        fields = "__all__"


class SoftwareStatementTemplateSerializer(
    serializers.ModelSerializer[SoftwareStatementTemplate]
):
    class Meta:
        model = SoftwareStatementTemplate
        fields = "__all__"
