from .models import DataspaceUser
from rest_framework import serializers
from rest_framework.authtoken.models import Token
from django.contrib.auth import get_user_model

UserModel = get_user_model()

class RegisterDataspaceUserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    class Meta:
        model = DataspaceUser
        fields = ['id', 'email', 'password']
    
    def create(self, validated_data):
        user = UserModel.objects.create_user(**validated_data)  # Use create_user method to handle password hashing
        return user

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