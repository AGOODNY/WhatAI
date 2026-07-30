from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .models import ChatRoom, Message
from .serializers import ChatRoomSerializer, MessageSerializer
from .services.message_service import MessageService
from django.utils import timezone
from django.db.models import Q
from apps.personas.models import Persona


# 获取所有聊天
class ChatRoomListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        rooms = ChatRoom.objects.filter(owner=request.user).order_by("-id")
        serializer = ChatRoomSerializer(rooms, many=True)
        return Response(serializer.data)


# 创建新聊天
class CreateChatRoomView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        name = request.data.get("name")
        scenario = request.data.get("scenario")
        persona_ids = request.data.get("persona_ids") or []
        user_participates = request.data.get("user_participates", False)

        if not isinstance(persona_ids, list):
            return Response(
                {"error": "persona_ids must be a list"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if len(persona_ids) < 2 or len(persona_ids) > 4:
            return Response(
                {"error": "Please choose 2-4 personas"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if len(persona_ids) != len(set(persona_ids)):
            return Response(
                {"error": "Please choose different personas"},
                status=status.HTTP_400_BAD_REQUEST
            )

        personas = list(
            Persona.objects.filter(
                Q(is_builtin=True) | Q(owner=request.user),
                id__in=persona_ids
            )
        )

        if len(personas) != len(persona_ids):
            return Response(
                {"error": "Invalid persona selection"},
                status=status.HTTP_400_BAD_REQUEST
            )

        room = ChatRoom.objects.create(
            name=name,
            scenario=scenario,
            owner=request.user,
            user_participates=bool(user_participates),
            is_active=True,
            started_at=timezone.now()
        )
        room.personas.set(personas)

        return Response({
            "id": room.id,
            "name": room.name
        })


# 获取某个聊天的消息
class MessageListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, room_id):
        room = ChatRoom.objects.filter(
            id=room_id,
            owner=request.user
        ).first()

        if not room:
            return Response({"error": "not found"}, status=404)

        last_id = request.GET.get("last_id")

        if last_id:
            messages = MessageService.get_messages_after(
                room_id, last_id
            )
        else:
            messages = MessageService.get_messages(room_id)

        serializer = MessageSerializer(messages, many=True)

        return Response(serializer.data)


class RoomStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, room_id):
        room = ChatRoom.objects.filter(
            id=room_id,
            owner=request.user,
        ).values("is_active", "user_participates").first()

        if not room:
            return Response({"error": "not found"}, status=status.HTTP_404_NOT_FOUND)
        return Response(room)


class SendMessageView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, room_id):
        room = ChatRoom.objects.filter(
            id=room_id,
            owner=request.user,
        ).first()

        if not room:
            return Response({"error": "not found"}, status=status.HTTP_404_NOT_FOUND)

        if not room.user_participates:
            return Response(
                {"error": "The user is not a participant in this room"},
                status=status.HTTP_403_FORBIDDEN,
            )

        if not room.is_active:
            return Response(
                {"error": "当前群聊已经暂停生成"},
                status=status.HTTP_409_CONFLICT,
            )

        content = str(request.data.get("content") or "").strip()
        reply_to_id = request.data.get("reply_to_id")
        if not content:
            return Response(
                {"error": "Message content is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if len(content) > 2000:
            return Response(
                {"error": "Message content is too long"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        reply_to = None
        if reply_to_id is not None:
            reply_to = Message.objects.filter(
                id=reply_to_id,
                room=room,
            ).first()
            if not reply_to:
                return Response(
                    {"error": "Invalid quoted message"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        message = MessageService.create_message(
            room.id,
            "user",
            content,
            reply_to=reply_to,
        )
        if not message:
            return Response(
                {"error": "Unable to create message"},
                status=status.HTTP_409_CONFLICT,
            )

        return Response(
            MessageSerializer(message).data,
            status=status.HTTP_201_CREATED,
        )


# 删除房间
class DeleteRoomView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, room_id):
        try:
            room = ChatRoom.objects.get(id=room_id, owner=request.user)
            room.delete()
            return Response({"msg": "deleted"})
        except ChatRoom.DoesNotExist:
            return Response({"error": "not found"}, status=404)


# 暂停与继续
class ToggleRoomActiveView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, room_id):
        try:
            room = ChatRoom.objects.get(id=room_id, owner=request.user)
            room.is_active = not room.is_active

            if room.is_active:
                room.started_at = timezone.now()

            room.save()

            return Response({
                "is_active": room.is_active
            })
        except ChatRoom.DoesNotExist:
            return Response({"error": "not found"}, status=404)
