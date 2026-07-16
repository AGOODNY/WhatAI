from django.db import models
from django.contrib.auth.models import User
from config.llm_models import DEFAULT_LLM_MODEL, LLM_MODEL_CHOICES


class UserProfile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="profile"
    )

    nickname = models.CharField(
        max_length=50,
        default="nickname"
    )

    avatar = models.ImageField(
        upload_to="avatars/",
        blank=True,
        null=True
    )

    llm_model = models.CharField(
        max_length=32,
        choices=LLM_MODEL_CHOICES,
        default=DEFAULT_LLM_MODEL,
    )

    def __str__(self):
        return self.user.username
