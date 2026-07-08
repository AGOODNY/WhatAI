import random
from typing import Dict, List, Optional


def _random_by_weight(weights: Dict[str, float]) -> Optional[str]:
    weights = {role: max(value, 0.01) for role, value in weights.items()}
    roles = list(weights.keys())
    values = list(weights.values())

    if not roles:
        return None

    return random.choices(roles, weights=values, k=1)[0]


def _mentioned_in_last_message(role: str, persona, history: List[Dict]) -> bool:
    if not history:
        return False

    text = history[-1].get("content", "")
    names = {role}

    if persona:
        names.add(str(getattr(persona, "id", "")))
        names.add(getattr(persona, "name", ""))
        legacy_role = getattr(persona, "legacy_role", None)
        if legacy_role:
            names.add(str(legacy_role))

    return any(name and name in text for name in names)


def choose_next_speaker(
    history: List[Dict],
    last_role: Optional[str] = None,
    roles: Optional[List[str]] = None,
    personas: Optional[List] = None,
) -> Optional[str]:
    active_roles = roles or ["A", "B", "C", "D"]
    if not active_roles:
        return None

    persona_by_role = {
        str(getattr(persona, "id", "")): persona
        for persona in personas or []
    }

    weights = {role: 1.0 for role in active_roles}

    recent_roles = [
        str(msg.get("role"))
        for msg in history[-8:]
        if msg.get("role") != "system"
    ]

    for role in active_roles:
        recent_count = recent_roles.count(role)
        if recent_count:
            weights[role] *= max(0.35, 1.0 - recent_count * 0.18)

        if role == last_role:
            weights[role] *= 0.08

        if role in recent_roles[-2:]:
            weights[role] *= 0.35

        if _mentioned_in_last_message(role, persona_by_role.get(role), history):
            weights[role] *= 1.5

    return _random_by_weight(weights)
