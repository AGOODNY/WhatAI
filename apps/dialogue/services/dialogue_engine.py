import random

from .prompt_builder import build_prompt
from .private_prompt_builder import (
    build_private_prompt
)

from .llm_client import LLMClient

from apps.memory.services.memory_manager import (
    MemoryManager
)

from apps.chat.models import ChatRoom

llm_client = LLMClient()


def generate_message(
    role,
    history,
    room_id=None,
    scenario=None,
    is_private=False,
):
    """
    通用消息生成
    """
    # 私聊
    if is_private:

        context = MemoryManager.build_context(
            history
        )

        prompt = build_private_prompt(
            role,
            context,
        )

    # 群聊
    else:

        if scenario is None:

            room = ChatRoom.objects.get(
                id=room_id
            )

            scenario = room.scenario

        context = MemoryManager.build_context(
            history
        )

        prompt = build_prompt(
            role,
            context,
            scenario
        )

    response = llm_client.generate(prompt)

    return response.strip()[:200]