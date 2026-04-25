from typing import List, Optional
from ..models import Message


class MessageService:

    @staticmethod
    def create_message(role: str, content: str) -> Message:
        return Message.objects.create(role=role, content=content)

    @staticmethod
    def get_all_messages(limit: int = 50) -> List[Message]:
        return Message.objects.all().order_by("-id")[:limit][::-1]

    @staticmethod
    def get_messages_after(last_id: Optional[int], limit: int = 50) -> List[Message]:
        if last_id:
            return Message.objects.filter(id__gt=last_id).order_by("id")[:limit]
        return MessageService.get_all_messages(limit=limit)