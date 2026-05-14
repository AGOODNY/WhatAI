from django.db import models
from django.contrib.auth.models import User


class PrivateChatRoom(models.Model):

    """
    私聊房间
    一个用户 + 一个AI角色
    """

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="private_rooms"
    )

    ai_role = models.CharField(max_length=1)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username}-{self.ai_role}"


class PrivateMessage(models.Model):

    """
    私聊消息
    """

    room = models.ForeignKey(
        PrivateChatRoom,
        on_delete=models.CASCADE,
        related_name="messages"
    )

    sender_type = models.CharField(
        max_length=10
    )
    """
    user / ai
    """

    content = models.TextField()

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return self.content[:20]