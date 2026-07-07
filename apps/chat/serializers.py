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
            "created_at",
            "is_active",
            "started_at",
            "personas",
        ]


class MessageSerializer(serializers.ModelSerializer):
    persona = PersonaSerializer(read_only=True)

    class Meta:
        model = Message
        fields = ["id", "role", "persona", "content", "timestamp"]
