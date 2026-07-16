import os
import dashscope
from dashscope import Generation
from django.conf import settings
from config.llm_models import DEFAULT_LLM_MODEL, normalize_llm_model


class LLMClient:

    def __init__(self):
        self.api_key = os.getenv("DASHSCOPE_API_KEY")

        if not self.api_key:
            print("[LLM] API key is not configured")
        else:
            dashscope.api_key = self.api_key

        # 主模型
        self.model = normalize_llm_model(
            getattr(settings, "LLM_MODEL", DEFAULT_LLM_MODEL)
        )

        print(f"[LLM] Current model: {self.model}")

    def generate(
        self,
        prompt: str,
        *,
        max_tokens: int = 80,
        temperature: float = 0.7,
        model: str = None,
    ) -> str:

        if not self.api_key:
            return "（未配置千问API）"

        selected_model = normalize_llm_model(model or self.model)

        def call_model(model_name):
            return Generation.call(
                model=model_name,
                prompt=prompt,
                max_tokens=max_tokens,
                temperature=temperature,
            )

        def extract_text(response):
            """
            ✅ 统一解析不同模型返回格式
            """
            try:
                # 情况1：qwen-turbo
                if hasattr(response.output, "text") and response.output.text:
                    return response.output.text.strip()

                # 情况2：deepseek / chat格式
                if hasattr(response.output, "choices"):
                    return response.output.choices[0].message.content.strip()

            except Exception as e:
                print("[PARSE ERROR]", e)

            return None

        try:
            # 1️⃣ 主模型
            response = call_model(selected_model)

            if response.status_code == 200:
                text = extract_text(response)
                if text:
                    return text
                else:
                    print(f"[LLM WARNING] {selected_model} 返回为空")

            else:
                print(f"[LLM ERROR - {selected_model}]", response)

            # 用户选择的模型必须被严格遵守，不静默切换到其他模型。
            return "（模型调用失败）"

        except Exception as e:
            print("[LLM EXCEPTION]", e)
            return "（调用异常）"
