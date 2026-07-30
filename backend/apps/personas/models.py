from django.conf import settings
from django.db import models


class Persona(models.Model):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="personas",
        blank=True,
        null=True,
    )
    name = models.CharField(max_length=80)
    avatar = models.CharField(max_length=255, blank=True, default="")
    description = models.TextField(blank=True, default="")
    speaking_style = models.TextField(blank=True, default="")
    personality_prompt = models.TextField(blank=True, default="")
    is_builtin = models.BooleanField(default=False)
    legacy_role = models.CharField(
        max_length=16,
        blank=True,
        null=True,
        unique=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-is_builtin", "created_at", "id"]

    def __str__(self):
        return self.name

    @property
    def avatar_url(self):
        if self.avatar:
            return self.avatar
        if self.legacy_role:
            return f"/avatars/{self.legacy_role}.jpg"
        return "/avatars/default.jpg"
