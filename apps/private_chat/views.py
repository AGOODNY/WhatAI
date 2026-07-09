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

        persona_id = request.data.get("persona_id")
        ai_role = request.data.get("ai_role")

        try:
            room = (
                PrivateChatService.create_room(
                    request.user,
                    persona_id=persona_id,
                    ai_role=ai_role
                )
            )
        except ValueError:
            return Response({"error": "Invalid persona"}, status=400)

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


class DeletePrivateRoomView(APIView):

    permission_classes = [IsAuthenticated]

    def delete(self, request, room_id):

        room = (
            PrivateChatRoom.objects.filter(
                id=room_id,
                user=request.user
            ).first()
        )

        if not room:
            return Response({"error": "not found"}, status=404)

        room.delete()

        return Response(status=204)


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

        user_msg, ai_messages = (
            PrivateChatService.send_message(
                room,
                content
            )
        )

        return Response({
            "user_message":
                PrivateMessageSerializer(
                    user_msg
                ).data,

            "ai_messages":
                PrivateMessageSerializer(
                    ai_messages,
                    many=True
                ).data,

            "ai_message":
                PrivateMessageSerializer(
                    ai_messages[0]
                ).data if ai_messages else None
        })
