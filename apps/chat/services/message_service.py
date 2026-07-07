from apps.chat.models import Message, ChatRoom
from django.db import IntegrityError


class MessageService:

    @staticmethod
    def get_messages(room_id, limit=30):
        return Message.objects.filter(
            room_id=room_id
        ).order_by("-id")[:limit][::-1]

    @staticmethod
    def get_messages_after(room_id, last_id):
        return Message.objects.filter(
            room_id=room_id,
            id__gt=last_id
        ).order_by("id")

    @staticmethod
    def create_message(room_id, role, content, persona=None):
        """
        安全创建消息（防止房间被删除）
        """
        try:
            # 先检查房间是否存在
            room = ChatRoom.objects.filter(id=room_id).first()
            if not room:
                return None

            return Message.objects.create(
                room=room,
                role=role,
                persona=persona,
                content=content
            )

        except IntegrityError:
            # 防止并发删除导致崩溃
            return None
