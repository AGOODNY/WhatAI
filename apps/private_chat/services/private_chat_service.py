from apps.private_chat.models import (
    PrivateChatRoom,
    PrivateMessage
)

from .ai_reply_service import (
    generate_ai_reply
)


class PrivateChatService:

    @staticmethod
    def create_room(user, ai_role):

        room, created = (
            PrivateChatRoom.objects.get_or_create(
                user=user,
                ai_role=ai_role
            )
        )

        return room

    @staticmethod
    def create_user_message(
        room,
        content
    ):

        return PrivateMessage.objects.create(
            room=room,
            sender_type="user",
            content=content
        )

    @staticmethod
    def create_ai_message(
        room,
        content
    ):

        return PrivateMessage.objects.create(
            room=room,
            sender_type="ai",
            content=content
        )

    @staticmethod
    def send_message(
        room,
        user_content
    ):

        # 用户消息
        PrivateChatService.create_user_message(
            room,
            user_content
        )

        # AI回复
        ai_reply = generate_ai_reply(room)

        ai_msg = (
            PrivateChatService.create_ai_message(
                room,
                ai_reply
            )
        )

        return ai_msg