import random
import time
from datetime import timedelta

from django.utils import timezone

from apps.chat.models import ChatRoom, Message
from apps.scheduler.services.scheduler import choose_next_speaker
from apps.dialogue.services.dialogue_engine import generate_group_messages
from apps.chat.services.message_service import MessageService
from apps.users.services.model_selection import get_user_llm_model


def _message_to_history_item(message):
    if message.persona:
        speaker = message.persona.name
    elif message.role == "user":
        profile = getattr(message.room.owner, "profile", None)
        speaker = getattr(profile, "nickname", "") or message.room.owner.username
    else:
        speaker = str(message.role)
    item = {
        "id": message.id,
        "role": str(message.persona_id or message.role),
        "speaker": speaker,
        "content": message.content,
        "timestamp": message.timestamp,
    }
    if message.reply_to:
        quoted = message.reply_to
        if quoted.persona:
            quoted_speaker = quoted.persona.name
        elif quoted.role == "user":
            profile = getattr(quoted.room.owner, "profile", None)
            quoted_speaker = (
                getattr(profile, "nickname", "")
                or quoted.room.owner.username
            )
        else:
            quoted_speaker = str(quoted.role)

        item.update({
            "reply_to_id": quoted.id,
            "reply_to_role": str(quoted.persona_id or quoted.role),
            "reply_to_speaker": quoted_speaker,
            "reply_to_content": quoted.content,
        })
    return item


def get_history(room_id, limit=100):
    messages = (
        Message.objects
        .filter(room_id=room_id)
        .select_related(
            "persona",
            "room__owner__profile",
            "reply_to__persona",
            "reply_to__room__owner__profile",
        )
        .order_by("-id")[:limit][::-1]
    )
    return [_message_to_history_item(message) for message in messages]


def _recent_message_count(history, seconds):
    cutoff = timezone.now() - timedelta(seconds=seconds)
    return sum(
        1 for item in history
        if item.get("timestamp") and item["timestamp"] >= cutoff
    )


def _is_direct_prompt(history):
    if not history:
        return False
    text = history[-1].get("content", "")
    return any(mark in text for mark in ("?", "？", "@"))


def _conversation_energy(history):
    if not history:
        return "opening"

    recent_count = _recent_message_count(history, 25)
    recent_speakers = {item.get("role") for item in history[-5:]}
    last_timestamp = history[-1].get("timestamp")
    age = (timezone.now() - last_timestamp).total_seconds() if last_timestamp else 0

    if _is_direct_prompt(history) or (recent_count >= 4 and len(recent_speakers) >= 2):
        return "hot"
    if age >= 18 or recent_count <= 1:
        return "cool"
    return "normal"


def _should_skip_turn(history):
    energy = _conversation_energy(history)
    probability = {
        "opening": 0.0,
        "hot": 0.05,
        "normal": 0.15,
        "cool": 0.32,
    }[energy]
    return random.random() < probability


def _next_delay_seconds(history, emitted_count=1):
    energy = _conversation_energy(history)

    if emitted_count > 1 or energy == "hot":
        delay = random.uniform(2.0, 5.0)
    elif energy == "cool":
        delay = random.uniform(12.0, 30.0)
    elif energy == "opening":
        delay = random.uniform(2.5, 5.0)
    else:
        delay = random.uniform(4.0, 10.0)

    # 偶尔自然停顿，形成真实聊天中的热度波动。
    if energy in {"hot", "normal"} and random.random() < 0.12:
        delay += random.uniform(8.0, 18.0)
    return delay


def _choose_ai_reply_target(history, role):
    """Choose a concrete recent message only when the turn looks like a reply."""
    if not history:
        return None

    last_message = history[-1]
    if str(last_message.get("role")) == str(role):
        return None

    text = last_message.get("content", "")
    explicitly_quoted_this_ai = (
        str(last_message.get("reply_to_role", "")) == str(role)
    )
    looks_direct = any(mark in text for mark in ("?", "？", "@"))

    if explicitly_quoted_this_ai or looks_direct:
        return last_message.get("id")
    if last_message.get("role") == "user" and random.random() < 0.72:
        return last_message.get("id")
    if random.random() < 0.2:
        return last_message.get("id")
    return None


def run_one_step_for_room(room, last_role=None):
    history = get_history(room.id)
    personas = list(room.personas.all())
    if not personas or _should_skip_turn(history):
        return last_role, 0

    role_ids = [str(persona.id) for persona in personas]
    role = choose_next_speaker(
        history,
        last_role,
        role_ids,
        personas=personas,
    )
    if not role:
        return last_role, 0

    persona = next((item for item in personas if str(item.id) == role), None)
    replies = generate_group_messages(
        role,
        history,
        room_id=room.id,
        scenario=room.scenario,
        participants=[
            *personas,
            *(
                [{
                    "name": (
                        getattr(getattr(room.owner, "profile", None), "nickname", "")
                        or room.owner.username
                    ),
                }]
                if room.user_participates
                else []
            ),
        ],
        model=get_user_llm_model(room.owner),
    )
    if not replies:
        return last_role, 0

    reply_to_id = _choose_ai_reply_target(history, role)
    reply_to = (
        Message.objects.filter(id=reply_to_id, room=room).first()
        if reply_to_id
        else None
    )
    messages = MessageService.create_messages(
        room.id,
        role,
        replies[:3],
        persona,
        reply_to=reply_to,
    )
    if not messages:
        return last_role, 0
    return role, len(messages)


def start_worker():
    last_roles = {}
    next_run_at = {}

    while True:
        now = time.monotonic()
        rooms = (
            ChatRoom.objects
            .filter(is_active=True, owner__isnull=False)
            .select_related("owner__profile")
            .prefetch_related("personas")
        )

        for room in rooms:
            if next_run_at.get(room.id, 0) > now:
                continue

            if room.started_at and timezone.now() - room.started_at > timedelta(minutes=10):
                room.is_active = False
                room.save(update_fields=["is_active"])
                print(f"[AUTO STOP] room {room.id} paused automatically")
                continue

            try:
                role, emitted_count = run_one_step_for_room(
                    room,
                    last_roles.get(room.id),
                )
                last_roles[room.id] = role
            except Exception as error:
                print(f"[Worker Error] room {room.id}:", error)
                emitted_count = 0

            history = get_history(room.id)
            next_run_at[room.id] = time.monotonic() + _next_delay_seconds(
                history,
                emitted_count=emitted_count,
            )

        time.sleep(1)
