from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .serializers import MessageSerializer
from .services.message_service import MessageService


class MessageListView(APIView):
    """
    GET /api/chat/messages/
    GET /api/chat/messages/?last_id=xxx
    """

    def get(self, request):
        last_id = request.query_params.get("last_id")

        try:
            last_id = int(last_id) if last_id else None
        except ValueError:
            return Response(
                {"error": "Invalid last_id"},
                status=status.HTTP_400_BAD_REQUEST
            )

        messages = MessageService.get_messages_after(last_id)
        serializer = MessageSerializer(messages, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)