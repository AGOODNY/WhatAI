from django.db import models
from django.utils import timezone

class ChatRoom(models.Model):
    """
    聊天房间（类似微信群）
    """
    name = models.CharField(max_length=100)
    scenario = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    is_active = models.BooleanField(default=True)

    started_at = models.DateTimeField(null=True, blank=True)

    personas = models.ManyToManyField(
        "personas.Persona",
        related_name="chat_rooms",
        blank=True
    )

    def __str__(self):
        return self.name


class Message(models.Model):
    """
    聊天消息
    """
    room = models.ForeignKey(
        ChatRoom,
        on_delete=models.CASCADE,
        related_name="messages"
    )

    role = models.CharField(max_length=64)  # legacy role or persona id
    persona = models.ForeignKey(
        "personas.Persona",
        on_delete=models.SET_NULL,
        related_name="messages",
        blank=True,
        null=True
    )
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.room.name}-{self.role}: {self.content[:20]}"
