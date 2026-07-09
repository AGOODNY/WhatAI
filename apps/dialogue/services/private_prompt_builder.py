from apps.personas.services import get_persona_by_token


def build_private_prompt(
    role,
    history,
    multi_bubble=False,
):
    persona = get_persona_by_token(role)
    recent_history = history[-20:]

    history_text = ""
    for msg in recent_history:
        history_text += f"{msg['role']}: {msg['content']}\n"

    bubble_rules = """
【回复气泡数量】

你要回复 1-4 个独立聊天气泡。
- 如果人格沉默寡言、话少、高冷、谨慎：优先 1 个气泡。
- 如果人格活泼、话多、碎碎念、外向：可以 2-4 个气泡。
- 每个气泡都是一条自然聊天消息，不要把一句话硬拆得很奇怪。
- 每个气泡建议不超过 60 个字。
- 只输出 JSON 字符串数组，例如：["嗯。", "我觉得可以。"]
- 不要输出 Markdown，不要输出解释，不要输出角色名。
""" if multi_bubble else """
【回复要求】

只输出一句自然聊天内容，不要解释，不要输出角色名。
"""

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

1. 像真人聊天，不要像 AI 助手。
2. 不要长篇大论。
3. 不要频繁使用语气词。
4. 不要重复句式。
5. 不要使用括号动作描写。
6. 不要提到不存在的人。
7. 根据人格自然决定回复长短和气泡数量。

{bubble_rules}

【聊天记录】

{history_text}
"""

    return prompt
