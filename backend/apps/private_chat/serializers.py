from rest_framework import serializers

from .models import (
    PrivateChatRoom,
    PrivateMessage
)
from apps.personas.serializers import PersonaSerializer


class PrivateChatRoomSerializer(
    serializers.ModelSerializer
):
    persona = PersonaSerializer(read_only=True)

    class Meta:
        model = PrivateChatRoom

        fields = "__all__"


class PrivateMessageSerializer(
    serializers.ModelSerializer
):

    class Meta:
        model = PrivateMessage

        fields = "__all__"
