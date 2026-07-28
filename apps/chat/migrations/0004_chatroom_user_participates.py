from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("chat", "0003_chatroom_owner"),
    ]

    operations = [
        migrations.AddField(
            model_name="chatroom",
            name="user_participates",
            field=models.BooleanField(default=False),
        ),
    ]
