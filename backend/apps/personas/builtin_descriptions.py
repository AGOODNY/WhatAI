"""User-facing descriptions for the built-in personas.

Edit this mapping when the short descriptions shown in the persona library
need to change. The API reads it at runtime, so display-only wording changes
do not require editing an old migration.
"""


BUILTIN_DESCRIPTIONS = {
    "A": "理性又有表现力，爱开玩笑，也很擅长在群聊中接住话题。",
    "B": "安静但不缺席，善于分析、熟悉网络梗，也很会顺着别人的想法继续聊。",
    "C": "反应快、表达短促而有活力，喜欢用跳跃又好玩的抽象类比。",
    "D": "活跃随性，擅长自嘲和吐槽，也很会让聊天自然继续下去。",
}


def get_builtin_description(legacy_role, fallback=""):
    return BUILTIN_DESCRIPTIONS.get(str(legacy_role or ""), fallback)

