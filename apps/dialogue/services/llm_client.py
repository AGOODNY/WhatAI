import os
from openai import OpenAI

class LLMClient:

    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        base_url = os.getenv("OPENAI_BASE_URL")

        if not api_key:
            print("[LLM] No API key found")
            self.client = None
            return

        self.client = OpenAI(
            api_key=api_key,
            base_url=base_url
        )

        # 推荐模型（便宜/免费）
        self.model = "meta-llama/llama-3-8b-instruct"

    def generate(self, prompt: str) -> str:

        if not self.client:
            return "（未配置API Key）"

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=60
            )

            return response.choices[0].message.content.strip()

        except Exception as e:
            print("[LLM ERROR]", e)
            return "（生成失败）"