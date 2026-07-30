from apps.chat.models import Message, ChatRoom
from django.db import IntegrityError
from django.db import transaction


class MessageService:

    @staticmethod
    def get_messages(room_id, limit=30):
        return Message.objects.filter(
            room_id=room_id
        ).select_related(
            "persona",
            "reply_to__persona",
            "reply_to__room__owner__profile",
        ).order_by("-id")[:limit][::-1]

    @staticmethod
    def get_messages_after(room_id, last_id):
        return Message.objects.filter(
            room_id=room_id,
            id__gt=last_id
        ).select_related(
            "persona",
            "reply_to__persona",
            "reply_to__room__owner__profile",
        ).order_by("id")

    @staticmethod
    def create_message(room_id, role, content, persona=None, reply_to=None):
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
                reply_to=reply_to,
                content=content
            )

        except IntegrityError:
            # 防止并发删除导致崩溃
            return None

    @staticmethod
    def create_messages(room_id, role, contents, persona=None, reply_to=None):
        contents = [content for content in contents if content]
        if not contents:
            return []

        try:
            with transaction.atomic():
                room = ChatRoom.objects.filter(id=room_id).first()
                if not room:
                    return []

                messages = []
                for index, content in enumerate(contents):
                    messages.append(Message.objects.create(
                        room=room,
                        role=role,
                        persona=persona,
                        reply_to=reply_to if index == 0 else None,
                        content=content,
                    ))
                return messages
        except IntegrityError:
            return []
