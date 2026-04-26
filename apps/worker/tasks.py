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

    MessageService.create_message(room_id, role, content)

    return role


def start_worker():
    last_roles = {}

    while True:
        rooms = ChatRoom.objects.all()

        for room in rooms:
            last_role = last_roles.get(room.id)

            new_role = run_one_step_for_room(room.id, last_role)

            last_roles[room.id] = new_role

        time.sleep(3)