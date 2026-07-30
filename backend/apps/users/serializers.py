from rest_framework import serializers
from django.contrib.auth.models import User

from .models import UserProfile
from config.llm_models import AVAILABLE_LLM_MODELS


class RegisterSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ["username", "password"]

        extra_kwargs = {
            "password": {
                "write_only": True
            }
        }

    def validate_username(self, value):

        if User.objects.filter(username=value).exists():

            raise serializers.ValidationError(
                "用户名已存在"
            )

        return value

    def create(self, validated_data):

        user = User.objects.create_user(
            username=validated_data["username"],
            password=validated_data["password"]
        )

        # 不要再手动创建 UserProfile
        # signals.py 会自动创建

        return user


class UserProfileSerializer(serializers.ModelSerializer):

    username = serializers.CharField(
        source="user.username"
    )

    avatar_url = serializers.SerializerMethodField()
    available_llm_models = serializers.SerializerMethodField()

    class Meta:
        model = UserProfile

        fields = [
            "username",
            "nickname",
            "avatar_url",
            "llm_model",
            "available_llm_models",
        ]

    def get_avatar_url(self, obj):

        request = self.context.get("request")

        if obj.avatar:

            return request.build_absolute_uri(
                obj.avatar.url
            )

        return None

    def get_available_llm_models(self, obj):
        return list(AVAILABLE_LLM_MODELS)
