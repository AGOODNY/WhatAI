from apps.dialogue.services.dialogue_engine import (
    generate_message
)

from apps.private_chat.models import (
    PrivateMessage
)

from apps.personas.personas import PERSONAS


def generate_ai_reply(room):

    messages = PrivateMessage.objects.filter(
        room=room
    ).order_by("id")

    history = []

    for msg in messages:

        if msg.sender_type == "user":

            history.append({
                "role": "USER",
                "content": msg.content
            })

        else:

            history.append({
                "role": room.ai_role,
                "content": msg.content
            })

    # AI角色名
    persona = PERSONAS[room.ai_role]

    # 私聊场景
    scenario = f"""
你正在和用户进行私聊。

你的名字是：
{persona["name"]}

这是一个一对一聊天。

请自然聊天。
不要像群聊一样发言。
不要提到不存在的人。
不要使用夸张AI语气。
"""

    content = generate_message(
        role=room.ai_role,
        history=history,
        scenario=scenario,
    )

    return content