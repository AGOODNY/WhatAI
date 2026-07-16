def _bullet_lines(items, fallback="暂无"):
    cleaned = [str(item).strip() for item in items or [] if str(item).strip()]
    if not cleaned:
        return fallback
    return "\n".join(f"- {item}" for item in cleaned)


def _participant_roles(participants):
    roles = set()
    names = []

    for participant in participants or []:
        if isinstance(participant, dict):
            legacy_role = participant.get("legacy_role")
            name = participant.get("display_name") or participant.get("name")
        else:
            legacy_role = getattr(participant, "legacy_role", None)
            name = getattr(participant, "name", None)

        if legacy_role:
            roles.add(str(legacy_role))
        if name:
            names.append(str(name))

    return roles, names


def build_persona_context(persona, mode, participants=None):
    speaking_style = persona.get("speaking_style", {})
    if not isinstance(speaking_style, dict):
        speaking_style = {"tone": str(speaking_style)}

    mode_rules = persona.get(
        "group_behavior" if mode == "group" else "private_behavior",
        [],
    )

    participant_roles, participant_names = _participant_roles(participants)
    relation_lines = []
    if mode == "group":
        for role, description in persona.get("relationships", {}).items():
            if str(role) in participant_roles and str(role) != str(persona.get("legacy_role")):
                relation_lines.append(description)

    core_traits = persona.get("core_traits", [])
    if not core_traits and persona.get("description"):
        core_traits = [persona["description"]]

    additional_prompt = ""
    if not persona.get("style") and persona.get("personality_prompt"):
        additional_prompt = f"\n【用户补充设定】\n{persona['personality_prompt']}\n"

    marker_text = "、".join(speaking_style.get("markers", [])) or "无固定口癖"
    example_text = _bullet_lines(persona.get("examples", []))
    participant_text = "、".join(participant_names) if participant_names else "未提供"

    relationship_section = ""
    if mode == "group":
        relationship_section = f"""
【群聊成员与关系】
当前成员：{participant_text}
{_bullet_lines(relation_lines, fallback='没有需要额外强调的关系；按普通熟人语气互动。')}
"""

    return f"""
【角色身份】
名字：{persona.get('display_name', 'Unknown')}
总体气质：{persona.get('style') or '自然、真实、有自己的反应'}

【性格与思考方式】
{_bullet_lines(core_traits)}
{_bullet_lines(persona.get('thinking_style', []))}

【当前模式下的行为】
{_bullet_lines(mode_rules)}

【说话风格】
语气：{speaking_style.get('tone') or '像普通人一样自然说话'}
长度倾向：{speaking_style.get('length') or '以简短口语为主'}
可能偶尔出现的表达：{marker_text}
这些表达只在语境合适时偶尔使用；不要为了证明身份而堆叠口癖。

【脱敏风格示例】
{example_text}
示例只用于理解节奏和措辞，禁止照抄，也不要围绕示例虚构背景。

【避免事项】
{_bullet_lines(persona.get('avoid', []))}
{additional_prompt}
{relationship_section}
""".strip()
