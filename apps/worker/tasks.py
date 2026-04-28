import time
from apps.chat.models import ChatRoom, Message
from apps.scheduler.services.scheduler import choose_next_speaker
from apps.dialogue.services.dialogue_engine import generate_message
from apps.chat.services.message_service import MessageService


def get_history(room_id):
    messages = Message.objects.filter(
        room_id=room_id
    ).order_by("-id")[:50][::-1]

    return [{"role": m.role, "content": m.content} for m in messages]


def run_one_step_for_room(room_id, last_role=None):
    history = get_history(room_id)

    role = choose_next_speaker(history, last_role)

    content = generate_message(role, history, room_id)

    msg = MessageService.create_message(room_id, role, content)
    if msg is None:
        return last_role

    return role


def start_worker():
    last_roles = {}

    while True:
        rooms = ChatRoom.objects.filter(is_active=True)

        for room in rooms:
            # 再次确认房间存在（防并发）
            if not ChatRoom.objects.filter(id=room.id).exists():
                continue

            last_role = last_roles.get(room.id)

            try:
                new_role = run_one_step_for_room(room.id, last_role)
                last_roles[room.id] = new_role
            except Exception as e:
                print(f"[Worker Error] room {room.id}:", e)

        time.sleep(3)