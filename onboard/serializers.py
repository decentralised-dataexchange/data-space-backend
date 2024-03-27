from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework.authtoken.models import Token

from .models import DataspaceUser

UserModel = get_user_model()


class RegisterDataspaceUserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = DataspaceUser
        fields = ["id", "email", "password", "name"]

    def create(self, validated_data):
        user = UserModel.objects.create_user(
            **validated_data
        )  # Use create_user method to handle password hashing
        return user


class DataspaceUserSerializer(serializers.ModelSerializer):

    class Meta:
        model = DataspaceUser
        fields = ["id", "email", "name"]
    
    def update(self, admin, validated_data):
        # Update only the "name" field if provided in the request
        admin.name = validated_data.get('name', admin.name)
        admin.save()
        return admin


class CustomTokenSerializer(serializers.ModelSerializer):
    user = DataspaceUserSerializer(many=False, read_only=True)

    class Meta:
        model = Token
        fields = ("key", "user")


class DataspaceUsersSerializer(serializers.ModelSerializer):

    class Meta:
        model = DataspaceUser
        fields = ["id", "email", "name"]
