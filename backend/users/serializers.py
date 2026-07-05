from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from rest_framework import serializers

from .constants import UserRole

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    groups = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "username", "email", "is_superuser", "date_joined", "groups"]
        read_only_fields = ["id", "is_superuser", "date_joined"]

    def get_groups(self, obj):
        return list(obj.groups.values_list("id", "name"))


class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    groups = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Group.objects.all(), required=False
    )

    class Meta:
        model = User
        fields = ["id", "username", "email", "password", "groups"]

    def create(self, validated_data):
        groups_data = validated_data.pop("groups", [])
        user = User.objects.create_user(**validated_data)
        if groups_data:
            user.groups.set(groups_data)
        return user


class UserRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ["username", "email", "password"]

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        user.groups.add(Group.objects.get(name=UserRole.USER))
        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    groups = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Group.objects.all(), required=False
    )

    class Meta:
        model = User
        fields = ["username", "email", "groups"]


class GroupSerializer(serializers.ModelSerializer):
    permissions = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Permission.objects.all(), required=False
    )

    class Meta:
        model = Group
        fields = ["id", "name", "permissions"]


class PermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permission
        fields = ["id", "name", "codename", "content_type"]
