import random
from typing import List, Dict, Optional


ROLES = ["A", "B", "C", "D"]

# 每个人的“话痨程度”（权重）
BASE_WEIGHTS = {
    "A": 1.0,
    "B": 1.3,  # 更爱说话
    "C": 0.7,
    "D": 1.2
}


def _penalize_last_speaker(weights: dict, last_role: Optional[str]):
    """
    防止连续说话：大幅降低上一个人的权重
    """
    if last_role and last_role in weights:
        weights[last_role] *= 0.1


def _boost_if_mentioned(weights: dict, history: List[Dict]):
    """
    如果有人被“点名”，提高他说话概率
    简单规则：文本中出现 A/B/C/D
    """
    if not history:
        return

    last_msg = history[-1]["content"]

    for role in ROLES:
        if role in last_msg:
            weights[role] *= 1.8


def _random_by_weight(weights: dict) -> str:
    roles = list(weights.keys())
    values = list(weights.values())

    total = sum(values)
    probs = [v / total for v in values]

    return random.choices(roles, probs)[0]


def choose_next_speaker(
    history: List[Dict],
    last_role: Optional[str] = None
) -> str:
    """
    输入：
        history: [{"role": "A", "content": "..."}]
        last_role: 上一个发言人

    输出：
        下一位发言人
    """

    # 1）基础权重
    weights = BASE_WEIGHTS.copy()

    # 2）避免连续说话
    _penalize_last_speaker(weights, last_role)

    # 3）被点名优先
    _boost_if_mentioned(weights, history)

    # 4）随机选择（带权重）
    next_role = _random_by_weight(weights)

    return next_role