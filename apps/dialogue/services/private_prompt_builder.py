from apps.personas.services import get_persona_by_token
from .persona_context import build_persona_context


def _format_private_history(history, persona):
    persona_tokens = {
        str(persona.get("id", "")),
        str(persona.get("name", "")),
        str(persona.get("legacy_role", "")),
    }
    lines = []

    for msg in history[-30:]:
        role = str(msg.get("role", ""))
        if role == "system":
            lines.append(f"[之前私聊摘要] {msg.get('content', '')}")
        elif role == "USER":
            lines.append(f"用户：{msg.get('content', '')}")
        elif role in persona_tokens:
            lines.append(f"{persona['display_name']}：{msg.get('content', '')}")
        else:
            lines.append(f"{msg.get('speaker') or role}：{msg.get('content', '')}")

    return "\n".join(lines) if lines else "暂无历史消息"


def build_private_prompt(
    role,
    history,
    multi_bubble=False,
    *,
    extra_context="",
    output_contract=None,
):
    persona = get_persona_by_token(role)
    persona_text = build_persona_context(persona, "private")
    history_text = _format_private_history(history, persona)

    if output_contract is None and multi_bubble:
        output_contract = """
根据这一刻的内容自然决定回复 1-4 个气泡。多数时候 1-2 个就够了；只有思路自然追加时才发更多。
只输出合法 JSON 字符串数组，例如：["嗯", "我觉得可以"]。
每个气泡尽量简短，不要把完整句子机械拆开。
"""
    elif output_contract is None:
        output_contract = "只输出一句自然聊天内容，不要使用 JSON，不要解释。"

    extra_context_section = (
        f"\n【当前额外情境】\n{extra_context.strip()}\n"
        if extra_context and extra_context.strip()
        else ""
    )

    return f"""
你正在和用户进行一对一私聊。请作为一个真实熟人回应，而不是 AI 助手或心理咨询模板。

{persona_text}

【私聊规则】
1. 明确回应用户真正说的内容，优先表达自己的判断、情绪、联想或补充，而不是把话题重新抛给用户。
2. 不长篇说教，不总结用户，不使用客服式分点建议，不频繁使用语气词。
3. 不凭空提到其他朋友、共同经历或用户没有提供的事实。
4. 可以使用聊天式括号补充或反讽，但禁止写动作、神态、心理或场景旁白；不要输出“（笑了一下）”“*点头*”之类的舞台说明。
5. 对认真或脆弱的话题减少玩梗，用符合人格的具体回应表达关心。
6. 默认不要反问。只有缺少关键信息、确实无法自然回应，或用户明确邀请你提问时，才偶尔问一个具体且有内容的问题。
7. 禁止用“你呢？”“你觉得呢？”“然后呢？”“为什么？”等通用反问作为结尾，也不要每次回答后追加问题来维持对话。
8. 多数回复应以陈述、回应、感叹或自然停顿结束；允许话题暂时结束，不必强行续聊。

【聊天记录】
{history_text}
{extra_context_section}

【本轮输出】
{output_contract.strip()}
不要输出名字、Markdown、规则或分析过程。
""".strip()
