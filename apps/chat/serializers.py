from rest_framework import serializers
from .models import ChatRoom, Message
from apps.personas.serializers import PersonaSerializer


class ChatRoomSerializer(serializers.ModelSerializer):
    personas = PersonaSerializer(many=True, read_only=True)

    class Meta:
        model = ChatRoom
        fields = [
            "id",
            "name",
            "scenario",
            "owner",
            "created_at",
            "is_active",
            "started_at",
            "user_participates",
            "personas",
        ]
        read_only_fields = ["owner"]


class MessageSerializer(serializers.ModelSerializer):
    persona = PersonaSerializer(read_only=True)
    is_user = serializers.SerializerMethodField()
    reply_to = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = [
            "id",
            "role",
            "persona",
            "is_user",
            "reply_to",
            "content",
            "timestamp",
        ]

    def get_is_user(self, obj):
        return obj.role == "user" and obj.persona_id is None

    def get_reply_to(self, obj):
        quoted = obj.reply_to
        if not quoted:
            return None

        is_user = quoted.role == "user" and quoted.persona_id is None
        if quoted.persona:
            display_name = quoted.persona.name
        elif is_user:
            profile = getattr(quoted.room.owner, "profile", None)
            display_name = (
                getattr(profile, "nickname", "")
                or quoted.room.owner.username
            )
        else:
            display_name = str(quoted.role)

        return {
            "id": quoted.id,
            "role": quoted.role,
            "is_user": is_user,
            "display_name": display_name,
            "content": quoted.content,
        }
