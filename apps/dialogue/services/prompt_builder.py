import re
from collections import Counter

from apps.personas.services import get_persona_by_token
from .persona_context import build_persona_context


def _speaker_name(msg):
    return msg.get("speaker") or msg.get("display_name") or str(msg.get("role", ""))


def _content_words(text):
    return re.findall(r"[\u4e00-\u9fff]{2,}|[A-Za-z0-9_]{3,}", text or "")


def _build_conversation_state(history):
    recent = [msg for msg in history[-12:] if msg.get("role") != "system"]
    if not recent:
        return {
            "last_speaker": "暂无",
            "last_message": "暂无",
            "recent_speakers": "暂无",
            "repeated_terms": "暂无",
        }

    words = []
    for msg in recent[-6:]:
        words.extend(_content_words(msg.get("content", "")))

    repeated = [
        word for word, count in Counter(words).most_common(5)
        if count >= 2 and len(word) >= 2
    ]

    return {
        "last_speaker": _speaker_name(recent[-1]),
        "last_message": recent[-1].get("content", ""),
        "recent_speakers": "、".join(_speaker_name(msg) for msg in recent[-6:]),
        "repeated_terms": "、".join(repeated[:3]) if repeated else "暂无",
    }


def _format_history(history):
    lines = []
    for msg in history[-30:]:
        if msg.get("role") == "system":
            lines.append(f"[之前话题摘要] {msg.get('content', '')}")
            continue
        quote_text = ""
        if msg.get("reply_to_id"):
            quote_text = (
                f" [引用 {msg.get('reply_to_speaker', '群成员')}："
                f"{msg.get('reply_to_content', '')}]"
            )
        lines.append(
            f"{_speaker_name(msg)}{quote_text}：{msg.get('content', '')}"
        )
    return "\n".join(lines) if lines else "暂无历史消息"


def build_prompt(role, history, scenario="", participants=None, target_bubbles=1):
    persona = get_persona_by_token(role)
    state = _build_conversation_state(history)
    history_text = _format_history(history)
    persona_text = build_persona_context(persona, "group", participants)
    target_bubbles = max(1, min(int(target_bubbles or 1), 3))

    return f"""
你正在参与一个真实熟人之间的多人群聊。你不是客服、旁白、写作助手，也不是在展示角色设定。

【群聊背景】
{scenario or '普通闲聊'}

{persona_text}

【当前聊天状态】
最近说话的人：{state['last_speaker']}
最近一句话：{state['last_message']}
最近发言顺序：{state['recent_speakers']}
近期已重复的词：{state['repeated_terms']}

【最近聊天记录】
{history_text}

【本轮任务】
1. 先判断真人在这个时刻最可能回应什么；可以接上一句、回应整体话题、补充小观点、轻微转移，或只给一个自然短反应。
2. 大多数气泡保持在 2-12 个中文字符左右；只有确实需要解释时才使用一条稍长消息。
3. 不要每次提问，不要逐字复述上一句，也不要抓住同一个词连续发挥。
4. 允许自然的单字或双字反应，但不得重复最近已经出现的同一短回复。
5. 可以使用聊天式括号补充或反讽，但禁止写动作、神态、心理或场景旁白；不要输出“（笑了一下）”“*点头*”之类的舞台说明。
6. 不提到聊天记录和背景中不存在的人、事件或共同经历。
7. 不输出角色名、规则、分析过程、Markdown 或代码围栏。

【输出格式】
本轮恰好发送 {target_bubbles} 个气泡。
只输出合法 JSON 字符串数组，例如：["嗯", "这个确实有点怪"]。
多气泡必须像思路自然追加，不能把一个完整句子机械拆开。
""".strip()
