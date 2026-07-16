import json
import random
import re

from .prompt_builder import build_prompt
from .private_prompt_builder import build_private_prompt
from .llm_client import LLMClient

from apps.memory.services.memory_manager import MemoryManager
from apps.personas.services import get_persona_by_token


llm_client = LLMClient()


FORBIDDEN_MARKERS = [
    "自然聊天规则",
    "本轮任务",
    "输出格式",
    "群聊背景",
    "最近聊天记录",
    "作为AI",
    "我是AI",
]

ACTION_WORDS = (
    "笑|微笑|苦笑|冷笑|大笑|叹气|叹息|沉默|点头|摇头|歪头|"
    "摸头|抱住|拥抱|挥手|摊手|耸肩|哭泣|脸红|眨眼|思考"
)


def _strip_role_prefix(text):
    return re.sub(r"^\s*[\w\u4e00-\u9fff]{1,12}\s*[:：]\s*", "", text)


def _strip_parenthetical_actions(text):
    pattern = rf"[（(]\s*(?:{ACTION_WORDS})(?:着|了|一下)?\s*[）)]"
    return re.sub(pattern, "", text, flags=re.IGNORECASE)


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
    return trim_to_sentence_boundary(text, max_chars=max_chars)


def _tokens(text):
    return set(re.findall(r"[\u4e00-\u9fff]{2,}|[A-Za-z0-9_]{3,}", text or ""))


def is_repetitive_reply(reply, history, window=6):
    reply = (reply or "").strip()
    if not reply:
        return True

    recent = [msg.get("content", "").strip() for msg in history[-window:]]
    if len(reply) <= 2:
        return reply in recent

    reply_tokens = _tokens(reply)
    for item in recent:
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


def _extract_json_array(text):
    text = (text or "").strip()
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\[[\s\S]*\]", text)
        if not match:
            return None
        try:
            data = json.loads(match.group(0))
        except json.JSONDecodeError:
            return None
    return data if isinstance(data, list) else None


def clean_reply_list(items, history=None, max_items=4, max_chars=60):
    history = history or []
    replies = []
    seen = set()

    for item in items or []:
        if not isinstance(item, str):
            continue

        reply = clean_reply(item, max_chars=max_chars)
        key = reply.strip()
        comparison_history = [
            *history,
            *({"content": existing} for existing in replies),
        ]

        if not key or key in seen or _looks_invalid(reply):
            continue
        if is_repetitive_reply(reply, comparison_history):
            continue

        seen.add(key)
        replies.append(reply)
        if len(replies) >= max_items:
            break
    return replies


def choose_bubble_count(persona):
    style = persona.get("speaking_style", {})
    weights = style.get("bubble_weights", [0.75, 0.20, 0.05]) if isinstance(style, dict) else [0.75, 0.20, 0.05]
    if len(weights) != 3 or sum(max(float(item), 0) for item in weights) <= 0:
        weights = [0.75, 0.20, 0.05]
    return random.choices([1, 2, 3], weights=weights, k=1)[0]


def generate_group_messages(
    role,
    history,
    *,
    room_id=None,
    scenario="",
    participants=None,
    target_bubbles=None,
    model=None,
):
    persona = get_persona_by_token(role)
    target_bubbles = target_bubbles or choose_bubble_count(persona)
    context = MemoryManager.build_context(
        history,
        conversation_key=room_id,
        mode="group",
        model_name=model,
    )
    prompt = build_prompt(
        role,
        context,
        scenario,
        participants=participants,
        target_bubbles=target_bubbles,
    )

    for _ in range(2):
        response = llm_client.generate(
            prompt,
            max_tokens=120,
            temperature=0.82,
            model=model,
        )
        parsed = _extract_json_array(response)
        if parsed is not None:
            replies = clean_reply_list(
                parsed,
                history=context,
                max_items=min(target_bubbles, 3),
                max_chars=60,
            )
        else:
            fallback = clean_reply(response, max_chars=60)
            replies = [] if _looks_invalid(fallback) or is_repetitive_reply(fallback, context) else [fallback]

        if replies:
            return replies
    return []


def generate_message(
    role,
    history,
    room_id=None,
    scenario=None,
    is_private=False,
    model=None,
):
    """Compatibility wrapper for callers that still expect one string."""
    if is_private:
        replies = generate_private_messages(role, history, room_id=room_id, model=model)
    else:
        replies = generate_group_messages(
            role,
            history,
            room_id=room_id,
            scenario=scenario or "",
            target_bubbles=1,
            model=model,
        )
    return replies[0] if replies else ""


def generate_private_messages(role, history, room_id=None, model=None):
    persona = get_persona_by_token(role)
    context = MemoryManager.build_context(
        history,
        conversation_key=room_id,
        mode="private",
        persona_name=persona.get("display_name", ""),
        model_name=model,
    )
    prompt = build_private_prompt(role, context, multi_bubble=True)
    response = llm_client.generate(
        prompt,
        max_tokens=160,
        temperature=0.76,
        model=model,
    )

    parsed = _extract_json_array(response)
    replies = clean_reply_list(parsed, history=context, max_items=4, max_chars=80)
    if replies:
        return replies

    fallback_prompt = build_private_prompt(role, context, multi_bubble=False)
    fallback_response = llm_client.generate(
        fallback_prompt,
        max_tokens=100,
        temperature=0.72,
        model=model,
    )
    fallback = clean_reply(fallback_response, max_chars=120)
    if _looks_invalid(fallback) or is_repetitive_reply(fallback, context):
        return []
    return [fallback]
