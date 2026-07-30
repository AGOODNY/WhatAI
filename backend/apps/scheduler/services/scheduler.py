import random
from typing import Dict, List, Optional

from apps.personas.services import get_persona_by_token


def _random_by_weight(weights: Dict[str, float]) -> Optional[str]:
    weights = {role: max(float(value), 0.01) for role, value in weights.items()}
    roles = list(weights.keys())
    if not roles:
        return None
    return random.choices(roles, weights=list(weights.values()), k=1)[0]


def _mentioned_in_last_message(persona, history: List[Dict]) -> bool:
    if not history or not persona:
        return False

    text = history[-1].get("content", "")
    name = getattr(persona, "name", "")
    return bool(name and name in text)


def choose_next_speaker(
    history: List[Dict],
    last_role: Optional[str] = None,
    roles: Optional[List[str]] = None,
    personas: Optional[List] = None,
) -> Optional[str]:
    active_roles = [str(role) for role in (roles or ["A", "B", "C", "D"])]
    if not active_roles:
        return None

    persona_by_role = {
        str(getattr(persona, "id", "")): persona
        for persona in personas or []
    }
    profile_by_role = {
        role: get_persona_by_token(persona_by_role.get(role) or role)
        for role in active_roles
    }

    weights = {
        role: float(profile_by_role[role].get("activity_weight", 1.0))
        for role in active_roles
    }
    recent_roles = [
        str(msg.get("role"))
        for msg in history[-10:]
        if msg.get("role") != "system"
    ]

    last_profile = profile_by_role.get(str(last_role))
    affinities = last_profile.get("reply_affinity", {}) if last_profile else {}
    quoted_role = (
        str(history[-1].get("reply_to_role", ""))
        if history
        else ""
    )

    for role in active_roles:
        recent_count = recent_roles.count(role)
        if recent_count:
            weights[role] *= max(0.28, 1.0 - recent_count * 0.17)

        if role == str(last_role) and role != quoted_role:
            weights[role] *= 0.04
        elif last_profile:
            legacy_role = str(profile_by_role[role].get("legacy_role") or "")
            affinity = affinities.get(legacy_role)
            if affinity is not None:
                weights[role] *= max(float(affinity) * 3.0, 0.25)

        if role in recent_roles[-2:]:
            weights[role] *= 0.4

        if _mentioned_in_last_message(persona_by_role.get(role), history):
            weights[role] *= 2.8

        # A user quoting an AI is a strong conversational signal that this
        # persona should get the next chance to answer.
        if role == quoted_role:
            weights[role] *= 7.0

    return _random_by_weight(weights)
