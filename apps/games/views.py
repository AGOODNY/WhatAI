from django.db.models import Q
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.personas.models import Persona

from .services import (
    choose_ai_move,
    generate_game_reply,
    has_five,
    validate_board,
)
from .idiom_services import respond_to_idiom_game, start_idiom_game


def _get_persona(request):
    return Persona.objects.filter(
        Q(is_builtin=True) | Q(owner=request.user),
        id=request.data.get("persona_id"),
    ).first()


class GomokuRespondView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        persona = _get_persona(request)
        if not persona:
            return Response({"error": "请选择有效的 AI 人格"}, status=400)

        try:
            board = validate_board(request.data.get("board"))
        except ValueError as exc:
            return Response({"error": str(exc)}, status=400)

        action = request.data.get("action", "chat")
        if action not in ("move", "chat"):
            return Response({"error": "无效操作"}, status=400)

        ai_move = None
        if action == "move" and not has_five(board, 1) and not has_five(board, 2):
            ai_move = choose_ai_move(board)
            if ai_move:
                board[ai_move["row"]][ai_move["col"]] = 2

        reply = generate_game_reply(
            persona=persona,
            user=request.user,
            board=board,
            history=request.data.get("history", []),
            message=str(request.data.get("message", ""))[:1000],
            action=action,
            ai_move=ai_move,
            force_reply=request.data.get("force_reply") is True,
        )

        return Response({
            "ai_move": ai_move,
            "reply": reply,
            "winner": (
                "ai" if has_five(board, 2)
                else "user" if has_five(board, 1)
                else None
            ),
        })


class IdiomStartView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        persona = _get_persona(request)
        if not persona:
            return Response({"error": "请选择有效的 AI 人格"}, status=400)

        return Response(start_idiom_game(
            persona=persona,
            user=request.user,
            history=request.data.get("history", []),
        ))


class IdiomRespondView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        persona = _get_persona(request)
        if not persona:
            return Response({"error": "请选择有效的 AI 人格"}, status=400)

        try:
            result = respond_to_idiom_game(
                persona=persona,
                user=request.user,
                game_token=request.data.get("game_token"),
                raw_chain=request.data.get("chain"),
                history=request.data.get("history", []),
                action=request.data.get("action", "chat"),
                message=str(request.data.get("message", ""))[:1000],
                timed_out=request.data.get("timed_out"),
            )
        except ValueError as exc:
            return Response({"error": str(exc)}, status=400)
        return Response(result)
