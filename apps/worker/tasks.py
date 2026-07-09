import random
import time
from datetime import timedelta

from django.utils import timezone

from apps.chat.models import ChatRoom, Message
from apps.scheduler.services.scheduler import choose_next_speaker
from apps.dialogue.services.dialogue_engine import generate_message
from apps.chat.services.message_service import MessageService


def _message_to_history_item(message):
    speaker = None
    if message.persona:
        speaker = message.persona.name

    return {
        "role": str(message.persona_id or message.role),
        "speaker": speaker or str(message.role),
        "content": message.content,
    }


def get_history(room_id):
    messages = (
        Message.objects
        .filter(room_id=room_id)
        .select_related("persona")
        .order_by("-id")[:50][::-1]
    )

    return [_message_to_history_item(message) for message in messages]


def _next_delay_seconds(history):
    if not history:
        return random.uniform(2.5, 5.0)

    recent = history[-4:]
    short_count = sum(1 for msg in recent if len(msg.get("content", "").strip()) <= 8)

    if short_count >= 3:
        return random.uniform(6.0, 11.0)

    return random.uniform(4.0, 9.0)


def _should_skip_turn(history):
    if not history:
        return False

    recent = history[-5:]
    short_count = sum(1 for msg in recent if len(msg.get("content", "").strip()) <= 8)

    if short_count >= 3:
        return random.random() < 0.4

    return random.random() < 0.18


def run_one_step_for_room(room_id, last_role=None):
    history = get_history(room_id)
    room = ChatRoom.objects.filter(id=room_id, owner__isnull=False).first()
    if not room:
        return last_role

    personas = list(room.personas.all())
    if not personas:
        return last_role

    if _should_skip_turn(history):
        return last_role

    role_ids = [str(persona.id) for persona in personas]

    role = choose_next_speaker(
        history,
        last_role,
        role_ids,
        personas=personas,
    )
    if not role:
        return last_role

    persona = next(
        (item for item in personas if str(item.id) == role),
        None
    )

    content = generate_message(role, history, room_id)
    if not content:
        return last_role

    msg = MessageService.create_message(room_id, role, content, persona)
    if msg is None:
        return last_role

    return role


def start_worker():
    last_roles = {}
    next_run_at = {}

    while True:
        now = time.monotonic()
        rooms = ChatRoom.objects.filter(is_active=True, owner__isnull=False)

        for room in rooms:
            if next_run_at.get(room.id, 0) > now:
                continue

            if not ChatRoom.objects.filter(id=room.id).exists():
                continue

            if room.started_at:
                if timezone.now() - room.started_at > timedelta(minutes=10):
                    room.is_active = False
                    room.save()
                    print(f"[AUTO STOP] room {room.id} paused automatically")
                    continue

            last_role = last_roles.get(room.id)
            history = get_history(room.id)

            try:
                new_role = run_one_step_for_room(room.id, last_role)
                last_roles[room.id] = new_role
            except Exception as e:
                print(f"[Worker Error] room {room.id}:", e)

            next_run_at[room.id] = time.monotonic() + _next_delay_seconds(history)

        time.sleep(1)
