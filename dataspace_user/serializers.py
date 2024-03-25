from .models import DataspaceUser
from rest_framework import serializers
from rest_framework.authtoken.models import Token


class RegisterDataspaceUserSerializer(serializers.ModelSerializer):

    class Meta:
        model = DataspaceUser
        fields = ['id', 'email', 'password']

class DataspaceUserSerializer(serializers.ModelSerializer):

    class Meta:
        model = DataspaceUser
        fields = ['id', 'email', 'fullname', 'address', 'country']


class CustomTokenSerializer(serializers.ModelSerializer):
    user = DataspaceUserSerializer(many=False, read_only=True)


    class Meta:
        model = Token
        fields = ('key', 'user')


class DataspaceUsersSerializer(serializers.ModelSerializer):

    class Meta:
        model = DataspaceUser
        fields = ['id', 'email', 'fullname', 'address', 'country']