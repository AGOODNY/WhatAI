from typing import List, Dict
from apps.chat.models import ChatRoom
from .prompt_builder import build_prompt
from .llm_client import LLMClient
from apps.memory.services.memory_manager import MemoryManager

llm_client = LLMClient()


def generate_message(role, history, room_id):

    room = ChatRoom.objects.get(id=room_id)

    context = MemoryManager.build_context(history)

    prompt = build_prompt(role, context, room.scenario)

    response = llm_client.generate(prompt)

    return response.strip()[:50]