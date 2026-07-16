from .models import Persona
from .personas import get_persona


def build_persona_dict(persona):
    result = {
        "id": persona.id,
        "name": str(persona.id),
        "display_name": persona.name,
        "avatar": persona.avatar_url,
        "description": persona.description,
        "core_traits": [
            item.strip()
            for item in persona.description.splitlines()
            if item.strip()
        ],
        "speaking_style": {
            "tone": persona.speaking_style,
        },
        "personality_prompt": persona.personality_prompt,
        "legacy_role": persona.legacy_role,
        "style": "",
        "thinking_style": [],
        "group_behavior": [],
        "private_behavior": [],
        "relationships": {},
        "examples": [],
        "avoid": [],
        "activity_weight": 1.0,
        "reply_affinity": {},
    }

    if persona.is_builtin and persona.legacy_role:
        profile = get_persona(persona.legacy_role)
        if profile:
            result.update(profile)
            result.update({
                "id": persona.id,
                "name": str(persona.id),
                "display_name": persona.name,
                "avatar": persona.avatar_url,
                "legacy_role": persona.legacy_role,
                "personality_prompt": persona.personality_prompt,
            })

    return result


def get_persona_by_token(token):
    if isinstance(token, Persona):
        return build_persona_dict(token)

    persona = None

    if token is not None:
        token = str(token)
        if token.isdigit():
            persona = Persona.objects.filter(id=int(token)).first()
        if persona is None:
            persona = Persona.objects.filter(legacy_role=token).first()

    if persona:
        return build_persona_dict(persona)

    return {
        "name": str(token or ""),
        "display_name": str(token or "Unknown"),
        "avatar": "/avatars/default.jpg",
        "description": "",
        "core_traits": [],
        "speaking_style": {
            "tone": "",
        },
        "personality_prompt": "",
        "legacy_role": str(token or ""),
    }
