from django.db import migrations, models


SUPPORTED_MODELS = (
    "deepseek-v4-flash",
    "deepseek-v4-pro",
)


def migrate_legacy_model_selections(apps, schema_editor):
    user_profile = apps.get_model("users", "UserProfile")
    user_profile.objects.exclude(
        llm_model__in=SUPPORTED_MODELS,
    ).update(
        llm_model="deepseek-v4-flash",
    )


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0002_userprofile_llm_model"),
    ]

    operations = [
        migrations.RunPython(
            migrate_legacy_model_selections,
            migrations.RunPython.noop,
        ),
        migrations.AlterField(
            model_name="userprofile",
            name="llm_model",
            field=models.CharField(
                choices=[
                    ("deepseek-v4-flash", "deepseek-v4-flash"),
                    ("deepseek-v4-pro", "deepseek-v4-pro"),
                ],
                default="deepseek-v4-flash",
                max_length=32,
            ),
        ),
    ]

