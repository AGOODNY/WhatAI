from django.contrib import admin
from .models import Message


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("id", "role", "content", "timestamp")
    list_filter = ("role",)
    search_fields = ("content",)