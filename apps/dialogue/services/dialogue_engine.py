import re

from .prompt_builder import build_prompt
from .private_prompt_builder import build_private_prompt
from .llm_client import LLMClient

from apps.memory.services.memory_manager import MemoryManager
from apps.chat.models import ChatRoom

llm_client = LLMClient()


FORBIDDEN_MARKERS = [
    "自然聊天规则",
    "输出要求",
    "群聊背景",
    "最近聊天记录",
    "作为AI",
    "我是AI",
]


def _strip_role_prefix(text):
    return re.sub(r"^\s*[\w\u4e00-\u9fff]{1,12}\s*[:：]\s*", "", text)


def _strip_parenthetical_actions(text):
    text = re.sub(r"（[^）]{0,30}）", "", text)
    text = re.sub(r"\([^)]{0,30}\)", "", text)
    return text


def trim_to_sentence_boundary(text, max_chars=90):
    text = text.strip()
    if len(text) <= max_chars:
        return text

    clipped = text[:max_chars]
    last_stop = max(clipped.rfind(mark) for mark in "。！？!?")
    if last_stop >= 8:
        return clipped[:last_stop + 1].strip()

    return clipped.rstrip("，,、；;：:")


def clean_reply(text, max_chars=90):
    text = (text or "").strip()
    text = text.replace("\r", "\n")
    text = "\n".join(line.strip() for line in text.splitlines() if line.strip())
    text = _strip_role_prefix(text)
    text = _strip_parenthetical_actions(text)
    text = text.strip(" \n\t\"'")
    text = trim_to_sentence_boundary(text, max_chars=max_chars)
    return text


def _tokens(text):
    return set(re.findall(r"[\u4e00-\u9fff]{2,}|[A-Za-z0-9_]{3,}", text or ""))


def is_repetitive_reply(reply, history, window=5):
    reply = (reply or "").strip()
    if len(reply) <= 2:
        return True

    reply_tokens = _tokens(reply)
    recent = [msg.get("content", "") for msg in history[-window:]]

    for item in recent:
        item = item.strip()
        if not item:
            continue

        if reply == item:
            return True

        item_tokens = _tokens(item)
        if reply_tokens and item_tokens:
            overlap = len(reply_tokens & item_tokens) / max(len(reply_tokens), 1)
            if overlap >= 0.75:
                return True

    return False


def _looks_invalid(reply):
    if not reply:
        return True

    return any(marker in reply for marker in FORBIDDEN_MARKERS)


def generate_message(
    role,
    history,
    room_id=None,
    scenario=None,
    is_private=False,
):
    if is_private:
        context = MemoryManager.build_context(history)
        prompt = build_private_prompt(role, context)
        response = llm_client.generate(prompt)
        return clean_reply(response, max_chars=120)

    if scenario is None:
        room = ChatRoom.objects.get(id=room_id)
        scenario = room.scenario

    context = MemoryManager.build_context(history)
    prompt = build_prompt(role, context, scenario)

    for _ in range(2):
        response = llm_client.generate(prompt)
        reply = clean_reply(response, max_chars=90)

        if not _looks_invalid(reply) and not is_repetitive_reply(reply, history):
            return reply

    return ""
