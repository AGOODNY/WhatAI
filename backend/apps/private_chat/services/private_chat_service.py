from django.db.models import Q

from apps.personas.models import Persona
from apps.private_chat.models import (
    PrivateChatRoom,
    PrivateMessage,
)
from apps.private_chat.services.ai_reply_service import generate_ai_replies


class PrivateChatService:

    @staticmethod
    def create_room(user, persona_id=None, ai_role=None):
        persona = None

        if persona_id:
            persona = Persona.objects.filter(
                Q(is_builtin=True) | Q(owner=user),
                id=persona_id,
            ).first()
        elif ai_role:
            persona = Persona.objects.filter(
                is_builtin=True,
                legacy_role=ai_role,
            ).first()

        if not persona:
            raise ValueError("Invalid persona")

        count = PrivateChatRoom.objects.filter(
            user=user,
            persona=persona,
        ).count()

        room = PrivateChatRoom.objects.create(
            user=user,
            ai_role=persona.legacy_role or str(persona.id),
            persona=persona,
            title=f"和 {persona.name} 的聊天 {count + 1}",
        )

        return room

    @staticmethod
    def send_message(room, content):
        user_msg = PrivateMessage.objects.create(
            room=room,
            sender_type="user",
            content=content,
        )

        ai_replies = generate_ai_replies(room)

        ai_messages = [
            PrivateMessage.objects.create(
                room=room,
                sender_type="ai",
                content=reply,
            )
            for reply in ai_replies[:4]
            if reply
        ]

        return user_msg, ai_messages
