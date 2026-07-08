from typing import Dict, List

from apps.dialogue.services.llm_client import LLMClient

llm_client = LLMClient()


class MemoryManager:
    MAX_HISTORY = 20
    RECENT_KEEP = 10

    @staticmethod
    def build_context(messages: List[Dict]) -> List[Dict]:
        if not messages:
            return []

        if len(messages) <= MemoryManager.MAX_HISTORY:
            return messages[-MemoryManager.MAX_HISTORY:]

        summary_part = messages[:-MemoryManager.RECENT_KEEP]
        recent_part = messages[-MemoryManager.RECENT_KEEP:]
        summary_text = MemoryManager._summarize(summary_part)

        return [
            {
                "role": "system",
                "content": f"之前聊天的自然摘要：{summary_text}",
            },
            *recent_part,
        ]

    @staticmethod
    def _speaker_name(msg: Dict) -> str:
        return msg.get("speaker") or msg.get("display_name") or str(msg.get("role", ""))

    @staticmethod
    def _summarize(messages: List[Dict]) -> str:
        history_text = ""
        for msg in messages:
            history_text += f"{MemoryManager._speaker_name(msg)}：{msg.get('content', '')}\n"

        prompt = f"""
请总结以下多人群聊，重点保留“话题如何推进”，而不是逐条复述。

需要包含：
- 大家正在聊什么
- 最近形成的共同关注点或分歧
- 哪些点已经聊过，不要让后续角色反复抓着说
- 当前可以自然接下去的方向

聊天记录：
{history_text}

请用 80-120 字中文输出摘要：
"""

        result = llm_client.generate(prompt)
        return result.strip() if result else "之前聊过一些内容，但摘要失败。"
