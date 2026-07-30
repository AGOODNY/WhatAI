from django.db import migrations, models
import django.db.models.deletion


def map_existing_private_rooms(apps, schema_editor):
    Persona = apps.get_model("personas", "Persona")
    PrivateChatRoom = apps.get_model("private_chat", "PrivateChatRoom")

    builtin = {
        persona.legacy_role: persona
        for persona in Persona.objects.filter(is_builtin=True)
    }

    for room in PrivateChatRoom.objects.all():
        persona = builtin.get(room.ai_role)
        if persona:
            room.persona = persona
            room.save(update_fields=["persona"])


def unmap_existing_private_rooms(apps, schema_editor):
    PrivateChatRoom = apps.get_model("private_chat", "PrivateChatRoom")
    PrivateChatRoom.objects.update(persona=None)


class Migration(migrations.Migration):

    dependencies = [
        ("personas", "0001_initial"),
        ("private_chat", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="privatechatroom",
            name="ai_role",
            field=models.CharField(max_length=64),
        ),
        migrations.AddField(
            model_name="privatechatroom",
            name="persona",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="private_rooms", to="personas.persona"),
        ),
        migrations.RunPython(map_existing_private_rooms, unmap_existing_private_rooms),
    ]
