from apps.personas.personas import get_persona


def build_prompt(role, history, scenario=""):

    persona = get_persona(role)

    history_text = ""

    for msg in history:
        if msg["role"] == "system":
            history_text += f"[总结]: {msg['content']}\n"
        else:
            history_text += f"{msg['role']}: {msg['content']}\n"

    prompt = f"""
你在一个群聊中。

聊天背景：
{scenario}

你的身份：
名字：{persona['name']}
性格：{persona['style']}
说话风格：{persona['speaking_style']}
人格特点：{persona['personality']}

聊天记录：
{history_text}

请自然回复一句，不要重复别人说过的话：
"""

    return prompt