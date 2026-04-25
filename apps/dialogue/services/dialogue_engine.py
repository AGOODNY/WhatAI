from typing import List, Dict

from .prompt_builder import build_prompt
from .llm_client import LLMClient
from apps.memory.services.memory_manager import MemoryManager

llm_client = LLMClient()


def generate_message(role: str, history: List[Dict]) -> str:
    """
    核心流程：
    1. memory处理历史（压缩/截断）
    2. 构建prompt
    3. 调用LLM
    4. 返回结果
    """

    # === 关键变化：引入 memory ===
    context = MemoryManager.build_context(history)

    prompt = build_prompt(role, context)

    response = llm_client.generate(prompt)

    # 清洗输出
    response = response.strip().replace("\n", "")

    if len(response) > 50:
        response = response[:50]

    return response if response else "..."