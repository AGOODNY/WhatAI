import re
from collections import Counter

from apps.personas.services import get_persona_by_token


def _speaker_name(msg):
    return msg.get("speaker") or msg.get("display_name") or str(msg.get("role", ""))


def _content_words(text):
    return re.findall(r"[\u4e00-\u9fff]{2,}|[A-Za-z0-9_]{3,}", text or "")


def _build_conversation_state(history):
    recent = [msg for msg in history[-10:] if msg.get("role") != "system"]
    if not recent:
        return {
            "last_speaker": "暂无",
            "last_message": "暂无",
            "recent_speakers": "暂无",
            "repeated_terms": "暂无",
            "is_stalled": "否",
        }

    words = []
    for msg in recent[-6:]:
        words.extend(_content_words(msg.get("content", "")))

    repeated = [
        word for word, count in Counter(words).most_common(5)
        if count >= 2 and len(word) >= 2
    ]

    speaker_names = [_speaker_name(msg) for msg in recent[-6:]]
    last_contents = [msg.get("content", "") for msg in recent[-4:]]
    short_replies = sum(1 for item in last_contents if len(item.strip()) <= 8)
    is_stalled = short_replies >= 3 or bool(repeated[:2])

    return {
        "last_speaker": _speaker_name(recent[-1]),
        "last_message": recent[-1].get("content", ""),
        "recent_speakers": "、".join(speaker_names),
        "repeated_terms": "、".join(repeated[:3]) if repeated else "暂无",
        "is_stalled": "是" if is_stalled else "否",
    }


def _format_history(history):
    lines = []
    for msg in history[-20:]:
        if msg.get("role") == "system":
            lines.append(f"[之前话题摘要] {msg.get('content', '')}")
            continue

        lines.append(f"{_speaker_name(msg)}：{msg.get('content', '')}")

    return "\n".join(lines) if lines else "暂无历史消息"


def build_prompt(role, history, scenario=""):
    persona = get_persona_by_token(role)
    state = _build_conversation_state(history)
    history_text = _format_history(history)
    traits = "、".join(persona.get("core_traits", [])[:3]) or "自然、真实、有自己的反应"
    tone = persona.get("speaking_style", {}).get("tone", "") or "像普通人一样自然说话"

    return f"""
你正在参与一个多人群聊。请像真实的人一样聊天，不要像客服、旁白或写作助手。

【群聊背景】
{scenario or "普通闲聊"}

【你的身份】
名字：{persona["display_name"]}
性格要点：{traits}
说话倾向：{tone}
补充设定：{persona.get("personality_prompt", "") or "无"}

【当前聊天状态】
最近说话的人：{state["last_speaker"]}
最近一句话：{state["last_message"]}
最近发言顺序：{state["recent_speakers"]}
最近重复出现的词：{state["repeated_terms"]}
话题是否有点卡住：{state["is_stalled"]}

【最近聊天记录】
{history_text}

【自然聊天规则】
1. 你可以接上一句，也可以回应整体话题、补充一个小观点、轻微转移话题，或用很短的自然反应带过。
2. 不要逐字抠最近一句里的几个字，不要围绕同一个词连续发挥。
3. 不要每次都提问；更常见的是顺着聊、评价一下、补充一点、开个轻微玩笑。
4. 如果话题卡住了，换一个贴近背景的小角度，而不是重复上一句话。
5. 不要复述聊天规则，不要输出角色名，不要写括号动作或旁白。
6. 避免和最近几条消息句式、情绪、关键词过于相似。

【输出】
只输出 {persona["display_name"]} 要发到群里的内容。
长度以 8-40 个中文字符为主；可以是一句，也可以是很短的两句。
"""
