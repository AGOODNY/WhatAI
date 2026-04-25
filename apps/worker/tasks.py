from apps.scheduler.services.scheduler import choose_next_speaker
from apps.chat.models import Message
from apps.dialogue.services.dialogue_engine import generate_message
from apps.chat.services.message_service import MessageService


def get_history():
    messages = Message.objects.all().order_by("-id")[:50][::-1]
    return [{"role": m.role, "content": m.content} for m in messages]


def run_one_step(last_role=None):
    history = get_history()

    role = choose_next_speaker(history, last_role)

    content = generate_message(role, history)

    MessageService.create_message(role, content)

    return role