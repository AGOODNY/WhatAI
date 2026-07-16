from apps.dialogue.services.dialogue_engine import generate_private_messages
from apps.private_chat.models import PrivateMessage
from apps.users.services.model_selection import get_user_llm_model


def generate_ai_replies(room):
    messages = PrivateMessage.objects.filter(
        room=room
    ).order_by("id")

    persona_token = str(room.persona_id or room.ai_role)
    history = []

    for msg in messages:
        history.append({
            "id": msg.id,
            "role": "USER" if msg.sender_type == "user" else persona_token,
            "content": msg.content,
        })

    return generate_private_messages(
        role=persona_token,
        history=history,
        room_id=room.id,
        model=get_user_llm_model(room.user),
    )
