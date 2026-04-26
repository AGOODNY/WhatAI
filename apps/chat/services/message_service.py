from apps.chat.models import Message, ChatRoom


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
    def create_message(room_id, role, content):
        return Message.objects.create(
            room_id=room_id,
            role=role,
            content=content
        )