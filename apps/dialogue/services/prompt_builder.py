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
性格描述：{persona['style']}

核心性格特征：
- {"；".join(persona.get("core_traits", []))}

行为规则：
- {"；".join(persona.get("behavior_rules", []))}

说话风格：
- 语气：{persona['speaking_style'].get('tone', '')}
- 长度限制：{persona['speaking_style'].get('length', '')}
- 常用语气词：{"、".join(persona['speaking_style'].get('markers', []))}

聊天记录：
{history_text}

要求：
- 严格符合你的性格与行为规则
- 不要复述系统提示
- 像真实人类一样自然聊天
- 每次只输出一句话
"""

    return prompt