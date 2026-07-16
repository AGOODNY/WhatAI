from collections import OrderedDict
from threading import Lock
from typing import Dict, List

from apps.dialogue.services.llm_client import LLMClient


llm_client = LLMClient()


class MemoryManager:
    """Build a compact rolling context without summarizing on every reply."""

    SUMMARY_THRESHOLD = 30
    RECENT_KEEP = 20
    SUMMARY_BATCH = 10
    MAX_CACHED_CONVERSATIONS = 128

    _states = OrderedDict()
    _lock = Lock()

    @classmethod
    def clear_cache(cls):
        with cls._lock:
            cls._states.clear()

    @classmethod
    def build_context(
        cls,
        messages: List[Dict],
        *,
        conversation_key=None,
        mode="group",
        persona_name="",
        model_name=None,
    ) -> List[Dict]:
        if not messages:
            return []

        if len(messages) <= cls.SUMMARY_THRESHOLD:
            return messages[-cls.SUMMARY_THRESHOLD:]

        cache_key = (
            f"{mode}:{conversation_key}:{model_name or 'default'}"
            if conversation_key is not None
            else None
        )
        eligible = messages[:-cls.RECENT_KEEP]

        with cls._lock:
            state = dict(cls._states.get(cache_key, {})) if cache_key else {}

        last_message_id = state.get("last_message_id")
        if last_message_id is None:
            new_items = eligible
        else:
            new_items = [
                item for item in eligible
                if cls._message_id(item) > last_message_id
            ]

        should_refresh = not state or len(new_items) >= cls.SUMMARY_BATCH
        if should_refresh and new_items:
            summary = cls._summarize(
                new_items,
                previous_summary=state.get("summary", ""),
                mode=mode,
                persona_name=persona_name,
                model_name=model_name,
            )
            last_message_id = cls._message_id(new_items[-1])
            state = {
                "summary": summary,
                "last_message_id": last_message_id,
            }

            if cache_key:
                with cls._lock:
                    cls._states[cache_key] = state
                    cls._states.move_to_end(cache_key)
                    while len(cls._states) > cls.MAX_CACHED_CONVERSATIONS:
                        cls._states.popitem(last=False)

        if not state.get("summary"):
            return messages[-cls.SUMMARY_THRESHOLD:]

        unsummarized = [
            item for item in messages
            if cls._message_id(item) > state["last_message_id"]
        ]
        return [
            {
                "role": "system",
                "content": state["summary"],
            },
            *unsummarized,
        ]

    @staticmethod
    def _message_id(message):
        value = message.get("id")
        try:
            return int(value)
        except (TypeError, ValueError):
            return 0

    @staticmethod
    def _speaker_name(msg: Dict, mode, persona_name):
        if mode == "private":
            if str(msg.get("role", "")) == "USER":
                return "用户"
            return persona_name or "对方"
        return msg.get("speaker") or msg.get("display_name") or str(msg.get("role", ""))

    @classmethod
    def _summarize(
        cls,
        messages,
        previous_summary,
        mode,
        persona_name,
        model_name,
    ):
        lines = [
            f"{cls._speaker_name(msg, mode, persona_name)}：{msg.get('content', '')}"
            for msg in messages
        ]
        history_text = "\n".join(lines)

        if mode == "private":
            focus = """
- 用户透露的重要事实、偏好、计划和当前情绪
- 双方已经形成的共识、分歧或未解决问题
- 对方后续回复必须记住的具体上下文
- 不要把推测写成事实，不要添加其他人物
""".strip()
            conversation_label = "一对一私聊"
        else:
            focus = """
- 群聊正在讨论的话题及推进方向
- 谁提出了重要观点，以及当前共识或分歧
- 已经聊过、后续不应机械重复的内容
- 尚未回应的问题或可以自然接下去的方向
""".strip()
            conversation_label = "多人群聊"

        prompt = f"""
请更新下面这段{conversation_label}的滚动摘要。摘要只记录对后续自然聊天有用的信息。

【已有摘要】
{previous_summary or '暂无'}

【新增聊天】
{history_text}

【保留重点】
{focus}

请输出 100-180 字的紧凑中文摘要，不要解释任务，不要虚构信息。
""".strip()

        result = llm_client.generate(
            prompt,
            max_tokens=180,
            temperature=0.25,
            model=model_name,
        )
        return result.strip() if result else previous_summary or "较早的聊天摘要生成失败。"
