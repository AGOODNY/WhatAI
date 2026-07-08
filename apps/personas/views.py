from django.db.models import Q
from django.core.files.storage import default_storage
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Persona
from .serializers import PersonaSerializer


def visible_personas(user):
    return Persona.objects.filter(
        Q(is_builtin=True) | Q(owner=user)
    ).order_by("-is_builtin", "created_at", "id")


def persona_payload(request):
    data = request.data.copy()
    avatar_file = request.FILES.get("avatar_file")

    if avatar_file:
        path = default_storage.save(f"persona_avatars/{avatar_file.name}", avatar_file)
        data["avatar"] = default_storage.url(path)

    data.pop("avatar_file", None)
    return data


class PersonaListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = PersonaSerializer(
            visible_personas(request.user),
            many=True,
        )
        return Response(serializer.data)

    def post(self, request):
        serializer = PersonaSerializer(data=persona_payload(request))
        if serializer.is_valid():
            persona = serializer.save(
                owner=request.user,
                is_builtin=False,
            )
            return Response(
                PersonaSerializer(persona).data,
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PersonaDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, request, persona_id):
        return Persona.objects.filter(
            id=persona_id,
            owner=request.user,
            is_builtin=False,
        ).first()

    def patch(self, request, persona_id):
        persona = self.get_object(request, persona_id)
        if not persona:
            return Response({"error": "not found"}, status=status.HTTP_404_NOT_FOUND)

        serializer = PersonaSerializer(
            persona,
            data=persona_payload(request),
            partial=True,
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, persona_id):
        persona = self.get_object(request, persona_id)
        if not persona:
            return Response({"error": "not found"}, status=status.HTTP_404_NOT_FOUND)

        persona.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
