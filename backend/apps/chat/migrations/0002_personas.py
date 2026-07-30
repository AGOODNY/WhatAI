from django.db import migrations, models
import django.db.models.deletion


def map_existing_chat_data(apps, schema_editor):
    Persona = apps.get_model("personas", "Persona")
    ChatRoom = apps.get_model("chat", "ChatRoom")
    Message = apps.get_model("chat", "Message")

    builtin = {
        persona.legacy_role: persona
        for persona in Persona.objects.filter(is_builtin=True)
    }

    for room in ChatRoom.objects.all():
        room.personas.add(*builtin.values())

    for message in Message.objects.all():
        persona = builtin.get(message.role)
        if persona:
            message.persona = persona
            message.save(update_fields=["persona"])


def unmap_existing_chat_data(apps, schema_editor):
    ChatRoom = apps.get_model("chat", "ChatRoom")
    Message = apps.get_model("chat", "Message")
    for room in ChatRoom.objects.all():
        room.personas.clear()
    Message.objects.update(persona=None)


class Migration(migrations.Migration):

    dependencies = [
        ("personas", "0001_initial"),
        ("chat", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="message",
            name="role",
            field=models.CharField(max_length=64),
        ),
        migrations.AddField(
            model_name="chatroom",
            name="personas",
            field=models.ManyToManyField(blank=True, related_name="chat_rooms", to="personas.persona"),
        ),
        migrations.AddField(
            model_name="message",
            name="persona",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="messages", to="personas.persona"),
        ),
        migrations.RunPython(map_existing_chat_data, unmap_existing_chat_data),
    ]
