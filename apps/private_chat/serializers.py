from rest_framework import serializers

from .models import (
    PrivateChatRoom,
    PrivateMessage
)


class PrivateChatRoomSerializer(
    serializers.ModelSerializer
):

    class Meta:
        model = PrivateChatRoom

        fields = "__all__"


class PrivateMessageSerializer(
    serializers.ModelSerializer
):

    class Meta:
        model = PrivateMessage

        fields = "__all__"