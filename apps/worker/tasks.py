import time
from apps.chat.models import ChatRoom, Message
from apps.scheduler.services.scheduler import choose_next_speaker
from apps.dialogue.services.dialogue_engine import generate_message
from apps.chat.services.message_service import MessageService
from django.utils import timezone
from datetime import timedelta

def get_history(room_id):
    messages = Message.objects.filter(
        room_id=room_id
    ).order_by("-id")[:50][::-1]

    return [
        {
            "role": str(m.persona_id or m.role),
            "content": m.content
        }
        for m in messages
    ]


def run_one_step_for_room(room_id, last_role=None):
    history = get_history(room_id)
    room = ChatRoom.objects.filter(id=room_id).first()
    if not room:
        return last_role

    personas = list(room.personas.all())
    if not personas:
        return last_role

    role_ids = [str(persona.id) for persona in personas]

    role = choose_next_speaker(history, last_role, role_ids)
    persona = next(
        (item for item in personas if str(item.id) == role),
        None
    )

    content = generate_message(role, history, room_id)

    msg = MessageService.create_message(room_id, role, content, persona)
    if msg is None:
        return last_role

    return role


def start_worker():
    last_roles = {}

    while True:
        rooms = ChatRoom.objects.filter(is_active=True)

        for room in rooms:
            # 再次确认房间存在
            if not ChatRoom.objects.filter(id=room.id).exists():
                continue

            #超时自动暂停（10分钟）
            if room.started_at:
                if timezone.now() - room.started_at > timedelta(minutes=10):
                    room.is_active = False
                    room.save()
                    print(f"[AUTO STOP] room {room.id} 已自动暂停")
                    continue

            last_role = last_roles.get(room.id)

            try:
                new_role = run_one_step_for_room(room.id, last_role)
                last_roles[room.id] = new_role
            except Exception as e:
                print(f"[Worker Error] room {room.id}:", e)

        time.sleep(3)
