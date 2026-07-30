from django.db import migrations


CHINESE_DESCRIPTIONS = {
    "A": "理性又有表现力，爱开玩笑，也很擅长在群聊中接住话题。",
    "B": "安静但不缺席，善于分析、熟悉网络梗，也很会顺着别人的想法继续聊。",
    "C": "反应快、表达短促而有活力，喜欢用跳跃又好玩的抽象类比。",
    "D": "活跃随性，擅长自嘲和吐槽，也很会让聊天自然继续下去。",
}

ENGLISH_DESCRIPTIONS = {
    "A": "Rational, expressive, playful, and highly engaged in group conversations.",
    "B": "Quietly active, analytical, meme-aware, and good at extending others' ideas.",
    "C": "Fast, fragmented, energetic, and prone to playful abstract comparisons.",
    "D": "Active, casual, self-deprecating, and good at keeping the chat alive.",
}


def update_descriptions(apps, descriptions):
    Persona = apps.get_model("personas", "Persona")
    for legacy_role, description in descriptions.items():
        Persona.objects.filter(
            is_builtin=True,
            legacy_role=legacy_role,
        ).update(description=description)


def use_chinese_descriptions(apps, schema_editor):
    update_descriptions(apps, CHINESE_DESCRIPTIONS)


def restore_english_descriptions(apps, schema_editor):
    update_descriptions(apps, ENGLISH_DESCRIPTIONS)


class Migration(migrations.Migration):

    dependencies = [
        ("personas", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(
            use_chinese_descriptions,
            restore_english_descriptions,
        ),
    ]

