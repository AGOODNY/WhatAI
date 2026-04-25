import os
import dashscope
from dashscope import Generation



class LLMClient:

    def __init__(self):
        self.api_key = os.getenv("DASHSCOPE_API_KEY")

        print("API KEY:", self.api_key)

        if not self.api_key:
            print("[LLM] 未配置通义千问API Key")
        else:
            dashscope.api_key = self.api_key

        self.model = "qwen-turbo"  # 免费模型

    def generate(self, prompt: str) -> str:

        if not self.api_key:
            return "（未配置千问API）"

        try:
            response = Generation.call(
                model=self.model,
                prompt=prompt,
                max_tokens=50,
                temperature=0.7
            )

            if response.status_code == 200:
                return response.output.text.strip()
            else:
                print("[LLM ERROR]", response)
                return "（生成失败）"

        except Exception as e:
            print("[LLM ERROR]", e)
            return "（调用异常）"