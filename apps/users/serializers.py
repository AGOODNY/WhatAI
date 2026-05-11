from rest_framework import serializers
from django.contrib.auth.models import User
from .models import UserProfile


class RegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["username", "password"]

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data["username"],
            password=validated_data["password"]
        )

        UserProfile.objects.create(user=user)

        return user


class UserProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username")

    class Meta:
        model = UserProfile
        fields = [
            "username",
            "nickname",
            "avatar"
        ]