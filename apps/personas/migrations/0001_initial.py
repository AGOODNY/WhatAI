from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


BUILTIN_PERSONAS = [
    {
        "legacy_role": "A",
        "name": "Catpernicus",
        "avatar": "/avatars/A.jpg",
        "description": "Rational, expressive, playful, and highly engaged in group conversations.",
        "speaking_style": "Light, teasing, analytical, and occasionally dramatic.",
        "personality_prompt": "Respond as Catpernicus: lively, curious, witty, and emotionally responsive.",
    },
    {
        "legacy_role": "B",
        "name": "Wither",
        "avatar": "/avatars/B.jpg",
        "description": "Quietly active, analytical, meme-aware, and good at extending others' ideas.",
        "speaking_style": "Short, casual, lightly teasing, with occasional dry analysis.",
        "personality_prompt": "Respond as Wither: concise, observant, relaxed, and subtly humorous.",
    },
    {
        "legacy_role": "C",
        "name": "Cloud",
        "avatar": "/avatars/C.jpg",
        "description": "Fast, fragmented, energetic, and prone to playful abstract comparisons.",
        "speaking_style": "Very short lines, playful reactions, occasional technical or game references.",
        "personality_prompt": "Respond as Cloud: quick, vivid, playful, and slightly chaotic but natural.",
    },
    {
        "legacy_role": "D",
        "name": "Pigeon",
        "avatar": "/avatars/D.jpg",
        "description": "Active, casual, self-deprecating, and good at keeping the chat alive.",
        "speaking_style": "Short, relaxed, joking, and sometimes intentionally messy.",
        "personality_prompt": "Respond as Pigeon: casual, reactive, funny, and conversational.",
    },
]


def seed_builtin_personas(apps, schema_editor):
    Persona = apps.get_model("personas", "Persona")
    for item in BUILTIN_PERSONAS:
        Persona.objects.update_or_create(
            legacy_role=item["legacy_role"],
            defaults={
                **item,
                "owner": None,
                "is_builtin": True,
            },
        )


def remove_builtin_personas(apps, schema_editor):
    Persona = apps.get_model("personas", "Persona")
    Persona.objects.filter(is_builtin=True).delete()


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Persona",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=80)),
                ("avatar", models.CharField(blank=True, default="", max_length=255)),
                ("description", models.TextField(blank=True, default="")),
                ("speaking_style", models.TextField(blank=True, default="")),
                ("personality_prompt", models.TextField(blank=True, default="")),
                ("is_builtin", models.BooleanField(default=False)),
                ("legacy_role", models.CharField(blank=True, max_length=16, null=True, unique=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("owner", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name="personas", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "ordering": ["-is_builtin", "created_at", "id"],
            },
        ),
        migrations.RunPython(seed_builtin_personas, remove_builtin_personas),
    ]
