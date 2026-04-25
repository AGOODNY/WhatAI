from typing import List, Dict

from apps.dialogue.services.llm_client import LLMClient

llm_client = LLMClient()

class MemoryManager:

    MAX_HISTORY = 20        # 最多保留多少条原始消息
    SUMMARY_TRIGGER = 15    # 超过多少条开始总结
    RECENT_KEEP = 8         # 总结后保留最近多少条

    @staticmethod
    def build_context(messages: List[Dict]) -> List[Dict]:
        """
        输入：
            messages: [{"role": "A", "content": "..."}]

        输出：
            context: 用于 prompt 的上下文（可能包含 summary）
        """
        if not messages:
            return []

        # 情况1：消息较少 → 直接截断
        if len(messages) <= MemoryManager.MAX_HISTORY:
            return messages[-MemoryManager.MAX_HISTORY:]

        # 情况2：消息较多 → 做 summary
        summary_part = messages[:-MemoryManager.RECENT_KEEP]
        recent_part = messages[-MemoryManager.RECENT_KEEP:]

        summary_text = MemoryManager._summarize(summary_part)

        # 用一个“系统消息”表示总结
        context = [
            {
                "role": "system",
                "content": f"以下是之前聊天的总结：{summary_text}"
            }
        ]

        context.extend(recent_part)

        return context

    @staticmethod
    def _summarize(messages: List[Dict]) -> str:
        """
        用 LLM 对历史进行压缩总结
        """
        history_text = ""
        for msg in messages:
            history_text += f"{msg['role']}: {msg['content']}\n"

        prompt = f"""
请总结以下群聊内容，保留关键信息：
- 谁在讨论什么
- 当前话题
- 人物关系或情绪

聊天记录：
{history_text}

总结（不超过100字）：
"""

        result = llm_client.generate(prompt)

        return result.strip() if result else "（总结失败）"