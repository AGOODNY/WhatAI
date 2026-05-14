from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import (
    IsAuthenticated
)

from .models import (
    PrivateChatRoom,
    PrivateMessage
)

from .serializers import (
    PrivateChatRoomSerializer,
    PrivateMessageSerializer
)

from .services.private_chat_service import (
    PrivateChatService
)


# 创建/获取私聊房间
class CreatePrivateRoomView(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request):

        ai_role = request.data.get("ai_role")

        room = (
            PrivateChatService.create_room(
                request.user,
                ai_role
            )
        )

        serializer = (
            PrivateChatRoomSerializer(room)
        )

        return Response(serializer.data)


# 获取我的私聊列表
class PrivateRoomListView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        rooms = (
            PrivateChatRoom.objects.filter(
                user=request.user
            )
        )

        serializer = (
            PrivateChatRoomSerializer(
                rooms,
                many=True
            )
        )

        return Response(serializer.data)


# 获取消息
class PrivateMessageListView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request, room_id):

        messages = (
            PrivateMessage.objects.filter(
                room_id=room_id
            ).order_by("id")
        )

        serializer = (
            PrivateMessageSerializer(
                messages,
                many=True
            )
        )

        return Response(serializer.data)


# 发送消息
class SendPrivateMessageView(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request, room_id):

        content = request.data.get("content")

        room = (
            PrivateChatRoom.objects.get(
                id=room_id,
                user=request.user
            )
        )

        ai_msg = (
            PrivateChatService.send_message(
                room,
                content
            )
        )

        serializer = (
            PrivateMessageSerializer(ai_msg)
        )

        return Response(serializer.data)