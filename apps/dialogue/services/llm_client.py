import os
import dashscope
from dashscope import Generation
from django.conf import settings


class LLMClient:

    def __init__(self):
        self.api_key = os.getenv("DASHSCOPE_API_KEY")

        print("API KEY:", self.api_key)

        if not self.api_key:
            print("[LLM] 未配置通义千问API Key")
        else:
            dashscope.api_key = self.api_key

        # 主模型
        self.model = getattr(settings, "LLM_MODEL", "qwen-turbo")

        # fallback 模型
        self.fallback_model = "qwen-turbo"

        print(f"[LLM] 当前模型: {self.model}")

    def generate(self, prompt: str) -> str:

        if not self.api_key:
            return "（未配置千问API）"

        def call_model(model_name):
            return Generation.call(
                model=model_name,
                prompt=prompt,
                max_tokens=50,
                temperature=0.7
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
            response = call_model(self.model)

            if response.status_code == 200:
                text = extract_text(response)
                if text:
                    return text
                else:
                    print(f"[LLM WARNING] {self.model} 返回为空")

            else:
                print(f"[LLM ERROR - {self.model}]", response)

            # 2️⃣ fallback
            print("[LLM] 尝试 fallback -> qwen-turbo")

            response = call_model(self.fallback_model)

            if response.status_code == 200:
                text = extract_text(response)
                if text:
                    return text

            print("[LLM ERROR - fallback]", response)
            return "（模型调用失败）"

        except Exception as e:
            print("[LLM EXCEPTION]", e)

            # 3️⃣ fallback（异常）
            try:
                print("[LLM] 异常 fallback -> qwen-turbo")

                response = call_model(self.fallback_model)

                if response.status_code == 200:
                    text = extract_text(response)
                    if text:
                        return text

            except Exception as e2:
                print("[LLM FALLBACK EXCEPTION]", e2)

            return "（调用异常）"