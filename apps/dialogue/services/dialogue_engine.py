import random
from typing import List, Dict
from apps.chat.models import ChatRoom
from .prompt_builder import build_prompt
from .llm_client import LLMClient
from apps.memory.services.memory_manager import MemoryManager

llm_client = LLMClient()


def generate_message(role, history, room_id):
    if random.random() < 0.3:
        return random.choice(
            [
                "草",
                "哈哈哈哈",
                "确实",
                "？",
                "6"
                "彳亍"
            ]
        )

    room = ChatRoom.objects.get(id=room_id)

    context = MemoryManager.build_context(history)

    prompt = build_prompt(role, context, room.scenario)

    response = llm_client.generate(prompt)

    return response.strip()[:50]