from rest_framework import serializers
import json
from .models import DataDisclosureAgreement

class DataDisclosureAgreementsSerializer(serializers.ModelSerializer):

    class Meta:
        model = DataDisclosureAgreement
        fields = '__all__'

class DataDisclosureAgreementSerializer(serializers.ModelSerializer):
    class Meta:
        model = DataDisclosureAgreement
        fields = ['dataDisclosureAgreementRecord']
