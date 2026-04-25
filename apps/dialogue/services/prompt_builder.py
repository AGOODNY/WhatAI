from typing import List, Dict
from apps.personas.personas import get_persona
# 人格设定
def build_prompt(role, history):

    persona = get_persona(role)

    history_text = ""

    for msg in history:
        if msg["role"] == "system":
            history_text += f"[总结]: {msg['content']}\n"
        else:
            history_text += f"{msg['role']}: {msg['content']}\n"

    prompt = f"""
你正在模拟一个群聊中的角色。

你的身份：
名字：{persona['name']}
性格：{persona['style']}
说话风格：{persona['speaking_style']}
人格特点：{persona['personality']}
在群里的关系：{persona['relationship']}

你可以参考的例句：
{chr(10).join(persona['example_lines'])}

群聊记录：
{history_text}

要求：
- 保持你的性格一致
- 不要重复别人说过的话
- 回复尽量自然，像真实聊天

请输出你的一句回复：
"""

    return prompt