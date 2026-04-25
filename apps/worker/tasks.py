import random
from apps.dialogue.services.dialogue_engine import generate_message
from apps.chat.models import Message
from apps.chat.services.message_service import MessageService

ROLES = ["A", "B", "C", "D"]


def choose_next_role(last_role=None):
    """
    简单调度策略：
    - 避免连续同一人说话
    """
    candidates = [r for r in ROLES if r != last_role] if last_role else ROLES
    return random.choice(candidates)


def get_history(limit=10):
    """
    获取最近的聊天记录，用于提供上下文
    """
    messages = Message.objects.all().order_by("-id")[:limit][::-1]
    return [{"role": m.role, "content": m.content} for m in messages]


def run_one_step(last_role=None):
    """
    执行一次：
    1. 选择角色
    2. 获取上下文
    3. 调用对话引擎生成消息
    4. 存储
    """
    role = choose_next_role(last_role)

    history = get_history()
    content = generate_message(role, history)

    MessageService.create_message(role, content)

    return role