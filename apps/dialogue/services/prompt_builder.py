from apps.personas.services import get_persona_by_token


def build_prompt(role, history, scenario=""):

    persona = get_persona_by_token(role)

    # ======================
    # 1. 构建简化历史（只保留最近）
    # ======================
    recent_history = history[-12:]  # 控制长度

    history_text = ""
    last_speaker = None
    last_message = ""

    for msg in recent_history:
        if msg["role"] == "system":
            history_text += f"[总结]: {msg['content']}\n"
        else:
            history_text += f"{msg['role']}: {msg['content']}\n"
            last_speaker = msg["role"]
            last_message = msg["content"]

    # ======================
    # 2. 行为规则（最关键）
    # ======================
    behavior_constraints = """
【聊天行为规则（必须遵守）】

1. 每次只说一句话（非常重要）
2. 长度控制在 5~20 字，极少超过30字
3. 不要刻意搞笑，不要每句都玩梗
4. 大多数时候是普通回应，少数时候才有亮点
5. 可以只回复短词（如：草 / 笑死 / 确实 / ？）
6. 可以无视部分消息，不必强行接话
7. 不要重复句式（禁止连续使用相同结构）
"""

    marker_constraints = """
【语气词规则（严格）】

1. 一句话最多使用一个语气词
2. 不要混用（如“草233ww😭”是错误的）
3. 可以完全不使用语气词
4. 语气词应该自然出现，而不是刻意添加
"""

    dialogue_state = f"""
【当前对话状态】

聊天背景：{scenario}

最近说话的人：{last_speaker}
你正在回复：{last_speaker} 的话
对方内容：{last_message}
"""

    # ======================
    # 3. 精简人格（避免AI过度表演）
    # ======================
    persona_block = f"""
【你的身份】

名字：{persona['display_name']}

性格要点：
- {"；".join(persona.get("core_traits", [])[:3])}

说话倾向：
- {persona['speaking_style'].get('tone', '')}

补充设定：
{persona.get('personality_prompt', '')}
"""

    # ======================
    # 4. 输出要求（收紧）
    # ======================
    output_rules = """
【输出要求】

- 只输出一句自然聊天内容
- 不要解释
- 不要复述规则
- 不要使用括号说明动作
- 不要总结
"""

    # ======================
    # 5. 最终 prompt
    # ======================
    prompt = f"""
你正在参与一个真实的多人群聊。

{behavior_constraints}

{marker_constraints}

{dialogue_state}

{persona_block}

【最近聊天记录】
{history_text}

{output_rules}
"""

    return prompt
