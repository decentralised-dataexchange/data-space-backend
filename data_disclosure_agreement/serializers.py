from rest_framework import serializers
import json
from .models import DataDisclosureAgreement, DataDisclosureAgreementTemplate

class DataDisclosureAgreementsSerializer(serializers.ModelSerializer):

    class Meta:
        model = DataDisclosureAgreement
        fields = '__all__'

class DataDisclosureAgreementSerializer(serializers.ModelSerializer):
    class Meta:
        model = DataDisclosureAgreement
        fields = ['dataDisclosureAgreementRecord','status','isLatestVersion']

class DataDisclosureAgreementTemplatesSerializer(serializers.ModelSerializer):

    class Meta:
        model = DataDisclosureAgreementTemplate
        fields = '__all__'

class DataDisclosureAgreementTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = DataDisclosureAgreementTemplate
        fields = ['dataDisclosureAgreementRecord','status','isLatestVersion']
