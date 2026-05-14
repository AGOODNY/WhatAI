import random

from .prompt_builder import build_prompt
from .llm_client import LLMClient

from apps.memory.services.memory_manager import MemoryManager
from apps.chat.models import ChatRoom

llm_client = LLMClient()


def generate_message(
    role,
    history,
    room_id=None,
    scenario=None,
):
    """
    通用消息生成函数

    支持：
    - 群聊（room_id）
    - 私聊（直接传 scenario）
    """

    # 偶尔短回复
    if random.random() < 0.3:
        return random.choice(
            [
                "草",
                "哈哈哈哈",
                "确实",
                "？",
                "6",
                "彳亍",
            ]
        )

    # 私聊优先使用传入 scenario
    if scenario is None:

        # 群聊模式
        room = ChatRoom.objects.get(id=room_id)

        scenario = room.scenario

    # 上下文
    context = MemoryManager.build_context(history)

    # prompt
    prompt = build_prompt(
        role,
        context,
        scenario
    )

    # LLM
    response = llm_client.generate(prompt)

    return response.strip()[:200]