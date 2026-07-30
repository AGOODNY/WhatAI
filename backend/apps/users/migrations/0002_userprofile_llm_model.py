from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="userprofile",
            name="llm_model",
            field=models.CharField(
                choices=[
                    ("deepseek-v4-flash", "deepseek-v4-flash"),
                    ("deepseek-v3.2", "deepseek-v3.2"),
                    ("deepseek-v4-pro", "deepseek-v4-pro"),
                ],
                default="deepseek-v3.2",
                max_length=32,
            ),
        ),
    ]
