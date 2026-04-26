from rest_framework.views import APIView
from rest_framework.response import Response

from .models import ChatRoom
from .serializers import ChatRoomSerializer, MessageSerializer
from .services.message_service import MessageService


# 获取所有聊天
class ChatRoomListView(APIView):
    def get(self, request):
        rooms = ChatRoom.objects.all().order_by("-id")
        serializer = ChatRoomSerializer(rooms, many=True)
        return Response(serializer.data)


# 创建新聊天
class CreateChatRoomView(APIView):
    def post(self, request):
        name = request.data.get("name")
        scenario = request.data.get("scenario")

        room = ChatRoom.objects.create(
            name=name,
            scenario=scenario
        )

        return Response({
            "id": room.id,
            "name": room.name
        })


# 获取某个聊天的消息
class MessageListView(APIView):
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