from apps.personas.services import get_persona_by_token


def build_private_prompt(
    role,
    history,
):
    persona = get_persona_by_token(role)

    recent_history = history[-20:]

    history_text = ""

    for msg in recent_history:

        history_text += (
            f"{msg['role']}: "
            f"{msg['content']}\n"
        )

    prompt = f"""
你正在和用户进行一对一私聊。

【你的身份】

名字：
{persona['display_name']}

性格：
{"；".join(persona.get("core_traits", []))}

说话风格：
{persona['speaking_style'].get('tone', '')}

补充设定：
{persona.get('personality_prompt', '')}

【重要规则】

1. 像真人聊天
2. 不要像AI
3. 不要过度玩梗
4. 不要长篇大论
5. 不要频繁使用语气词
6. 不要重复句式
7. 一次只回复一句
8. 长度控制在30字以内
9. 不要使用括号动作
10. 不要提到不存在的人

【聊天记录】

{history_text}

只输出回复内容：
"""

    return prompt
