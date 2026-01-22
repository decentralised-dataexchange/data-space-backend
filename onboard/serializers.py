from typing import Any

from rest_framework import serializers
from rest_framework.authtoken.models import Token

from .models import DataspaceUser


class RegisterDataspaceUserSerializer(serializers.ModelSerializer[DataspaceUser]):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = DataspaceUser
        fields = ["id", "email", "password", "name"]

    def create(self, validated_data: dict[str, Any]) -> DataspaceUser:
        # Use create_user method to handle password hashing
        user: DataspaceUser = DataspaceUser.objects.create_user(**validated_data)
        return user


class DataspaceUserSerializer(serializers.ModelSerializer[DataspaceUser]):
    class Meta:
        model = DataspaceUser
        fields = ["id", "email", "name"]

    def update(
        self, instance: DataspaceUser, validated_data: dict[str, Any]
    ) -> DataspaceUser:
        # Update only the "name" field if provided in the request
        instance.name = validated_data.get("name", instance.name)
        instance.save()
        return instance


class CustomTokenSerializer(serializers.ModelSerializer[Token]):
    user = DataspaceUserSerializer(many=False, read_only=True)

    class Meta:
        model = Token
        fields = ("key", "user")


class DataspaceUsersSerializer(serializers.ModelSerializer[DataspaceUser]):
    class Meta:
        model = DataspaceUser
        fields = ["id", "email", "name"]
