from apps.dialogue.services.dialogue_engine import generate_private_messages
from apps.private_chat.models import PrivateMessage


def generate_ai_replies(room):
    messages = PrivateMessage.objects.filter(
        room=room
    ).order_by("id")

    persona_token = str(room.persona_id or room.ai_role)
    history = []

    for msg in messages:
        history.append({
            "role": "USER" if msg.sender_type == "user" else persona_token,
            "content": msg.content,
        })

    return generate_private_messages(
        role=persona_token,
        history=history,
    )
