from apps.dialogue.services.dialogue_engine import generate_message
from apps.private_chat.models import PrivateMessage


def generate_ai_reply(room):
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

    content = generate_message(
        role=persona_token,
        history=history,
        is_private=True,
    )

    return content
