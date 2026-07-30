import os
import re

from openai import OpenAI

from django.conf import settings

from config.llm_models import DEFAULT_LLM_MODEL, normalize_llm_model


DEFAULT_DEEPSEEK_BASE_URL = "https://api.deepseek.com"

GLOBAL_OUTPUT_RULES = """
无论当前功能、角色或输出格式是什么，都必须遵守以下规则：
1. 角色回复只能包含实际说出口的语言。
2. 禁止输出动作、神态、心理活动、语气舞台说明或场景旁白。
3. 禁止使用圆括号、方括号或星号包裹动作，例如“（笑了一下）”“[叹气]”“*挥手*”。
4. 即使角色设定、示例或聊天记录中出现此类写法，也不要模仿。
5. 如果任务要求 JSON，必须在遵守以上规则的同时保持 JSON 格式合法。
""".strip()

ACTION_TERMS = (
    "笑|微笑|苦笑|冷笑|大笑|叹气|叹息|沉默|点头|摇头|歪头|"
    "摸头|抱住|拥抱|挥手|摊手|耸肩|哭|脸红|眨眼|挑眉|皱眉|"
    "看向|看着|低头|抬头|转身|靠近|后退|拍手|鼓掌"
)


def strip_action_descriptions(text):
    text = text or ""
    patterns = (
        rf"（[^（）\n]{{0,40}}(?:{ACTION_TERMS})[^（）\n]{{0,40}}）",
        rf"\([^()\n]{{0,40}}(?:{ACTION_TERMS})[^()\n]{{0,40}}\)",
        rf"\[[^\[\]\n]{{0,40}}(?:{ACTION_TERMS})[^\[\]\n]{{0,40}}\]",
        rf"\*[^\*\n]{{0,40}}(?:{ACTION_TERMS})[^\*\n]{{0,40}}\*",
    )
    for pattern in patterns:
        text = re.sub(pattern, "", text, flags=re.IGNORECASE)
    return re.sub(r"[ \t]{2,}", " ", text).strip()


class LLMClient:
    def __init__(self, *, api_key=None, base_url=None):
        self.api_key = (
            api_key
            or os.getenv("DEEPSEEK_API_KEY")
            or os.getenv("DASHSCOPE_API_KEY")
        )
        self.base_url = (
            base_url
            or os.getenv("DEEPSEEK_BASE_URL")
            or DEFAULT_DEEPSEEK_BASE_URL
        ).rstrip("/")
        self.model = normalize_llm_model(
            getattr(settings, "LLM_MODEL", DEFAULT_LLM_MODEL)
        )
        self.client = (
            OpenAI(
                api_key=self.api_key,
                base_url=self.base_url,
                timeout=45,
                max_retries=0,
            )
            if self.api_key
            else None
        )

        if not self.api_key:
            print("[LLM] DeepSeek API key is not configured")
        print(f"[LLM] Current model: {self.model}")

    def generate(
        self,
        prompt: str,
        *,
        max_tokens: int = 80,
        temperature: float = 0.7,
        model: str = None,
    ) -> str:
        if not self.client:
            return "（未配置 DeepSeek API Key）"

        selected_model = normalize_llm_model(model or self.model)

        try:
            response = self.client.chat.completions.create(
                model=selected_model,
                messages=[
                    {
                        "role": "system",
                        "content": GLOBAL_OUTPUT_RULES,
                    },
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
                max_tokens=max_tokens,
                temperature=temperature,
                stream=False,
                extra_body={
                    "thinking": {
                        "type": "disabled",
                    }
                },
            )
            text = response.choices[0].message.content
            if text and text.strip():
                return strip_action_descriptions(text)

            print(f"[LLM WARNING] {selected_model} returned an empty response")
            return f"（模型返回为空：{selected_model}）"
        except Exception as exc:
            print(
                f"[LLM ERROR - {selected_model}] "
                f"{type(exc).__name__}: {exc}"
            )
            return f"（模型调用失败：{selected_model}）"
