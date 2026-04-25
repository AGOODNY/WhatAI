from typing import List, Dict

from .prompt_builder import build_prompt
from .llm_client import LLMClient

llm_client = LLMClient()


def generate_message(role: str, history: List[Dict]) -> str:
    """
    核心流程：
    1. 构建prompt
    2. 调用LLM
    3. 返回结果
    """

    prompt = build_prompt(role, history)

    response = llm_client.generate(prompt)

    # 简单清洗
    response = response.strip().replace("\n", "")

    if len(response) > 50:
        response = response[:50]

    return response if response else "..."