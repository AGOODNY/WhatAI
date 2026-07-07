from rest_framework import serializers

from .models import Persona


class PersonaSerializer(serializers.ModelSerializer):
    avatar_url = serializers.CharField(read_only=True)

    class Meta:
        model = Persona
        fields = [
            "id",
            "name",
            "avatar",
            "avatar_url",
            "description",
            "speaking_style",
            "personality_prompt",
            "is_builtin",
            "legacy_role",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "avatar_url",
            "is_builtin",
            "legacy_role",
            "created_at",
        ]

    def validate_name(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Name is required")
        return value

    def validate(self, attrs):
        for field in ["description", "speaking_style", "personality_prompt", "avatar"]:
            if field in attrs and isinstance(attrs[field], str):
                attrs[field] = attrs[field].strip()
        return attrs
