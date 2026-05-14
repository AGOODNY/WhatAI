from apps.private_chat.models import (
    PrivateChatRoom,
    PrivateMessage
)

from apps.private_chat.services.ai_reply_service import (
    generate_ai_reply
)

from apps.personas.personas import PERSONAS


class PrivateChatService:

    @staticmethod
    def create_room(user, ai_role):

        count = (
            PrivateChatRoom.objects.filter(
                user=user,
                ai_role=ai_role
            ).count()
        )

        persona = PERSONAS[ai_role]

        title = (
            f"和{persona['display_name']}的聊天"
            f"{count + 1}"
        )

        room = PrivateChatRoom.objects.create(
            user=user,
            ai_role=ai_role,
            title=title
        )

        return room

    @staticmethod
    def send_message(room, content):

        user_msg = (
            PrivateMessage.objects.create(
                room=room,
                sender_type="user",
                content=content
            )
        )

        ai_reply = generate_ai_reply(room)

        ai_msg = (
            PrivateMessage.objects.create(
                room=room,
                sender_type="ai",
                content=ai_reply
            )
        )

        return user_msg, ai_msg