from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .models import ChatRoom
from .serializers import ChatRoomSerializer, MessageSerializer
from .services.message_service import MessageService
from django.utils import timezone


# 获取所有聊天
class ChatRoomListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        rooms = ChatRoom.objects.all().order_by("-id")
        serializer = ChatRoomSerializer(rooms, many=True)
        return Response(serializer.data)


# 创建新聊天
class CreateChatRoomView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        name = request.data.get("name")
        scenario = request.data.get("scenario")

        room = ChatRoom.objects.create(
            name=name,
            scenario=scenario,
            is_active=True,
            started_at=timezone.now()
        )

        return Response({
            "id": room.id,
            "name": room.name
        })


# 获取某个聊天的消息
class MessageListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, room_id):
        last_id = request.GET.get("last_id")

        if last_id:
            messages = MessageService.get_messages_after(
                room_id, last_id
            )
        else:
            messages = MessageService.get_messages(room_id)

        serializer = MessageSerializer(messages, many=True)

        return Response(serializer.data)


# 删除房间
class DeleteRoomView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, room_id):
        try:
            room = ChatRoom.objects.get(id=room_id)
            room.delete()
            return Response({"msg": "deleted"})
        except ChatRoom.DoesNotExist:
            return Response({"error": "not found"}, status=404)


# 暂停与继续
class ToggleRoomActiveView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, room_id):
        try:
            room = ChatRoom.objects.get(id=room_id)
            room.is_active = not room.is_active

            if room.is_active:
                room.started_at = timezone.now()

            room.save()

            return Response({
                "is_active": room.is_active
            })
        except ChatRoom.DoesNotExist:
            return Response({"error": "not found"}, status=404)