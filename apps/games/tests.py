from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import SimpleTestCase
from rest_framework.test import APITestCase

from apps.personas.models import Persona

from .services import choose_ai_move, has_five, validate_board


class GomokuServiceTests(SimpleTestCase):
    def empty_board(self):
        return [[0 for _ in range(15)] for _ in range(15)]

    def test_ai_finishes_a_winning_line(self):
        board = self.empty_board()
        for col in range(4, 8):
            board[7][col] = 2
            board[6][col] = 1

        move = choose_ai_move(board)
        board[move["row"]][move["col"]] = 2

        self.assertTrue(has_five(board, 2))

    def test_ai_blocks_users_immediate_win(self):
        board = self.empty_board()
        for col in range(4, 8):
            board[7][col] = 1
        for row, col in ((1, 1), (3, 12), (10, 2), (12, 11)):
            board[row][col] = 2

        move = choose_ai_move(board)

        self.assertIn((move["row"], move["col"]), {(7, 3), (7, 8)})

    def test_invalid_turn_counts_are_rejected(self):
        board = self.empty_board()
        board[7][7] = 1
        board[7][8] = 1

        with self.assertRaises(ValueError):
            validate_board(board)


class GomokuApiTests(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="gomoku-player",
            password="test-password",
        )
        self.persona = Persona.objects.create(
            name="棋友",
            description="沉着的五子棋对手",
            is_builtin=True,
        )
        self.client.force_authenticate(self.user)

    @patch(
        "apps.games.services.LLMClient.generate",
        return_value='{"speak": true, "content": "这步有点意思。"}',
    )
    def test_move_response_contains_legal_ai_move_and_reply(self, generate):
        board = [[0 for _ in range(15)] for _ in range(15)]
        board[7][7] = 1

        response = self.client.post(
            "/api/games/gomoku/respond/",
            {
                "persona_id": self.persona.id,
                "board": board,
                "history": [],
                "message": "我走天元。",
                "action": "move",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["reply"], "这步有点意思。")
        move = response.data["ai_move"]
        self.assertIsNotNone(move)
        self.assertEqual(board[move["row"]][move["col"]], 0)
        prompt = generate.call_args.args[0]
        self.assertIn("你正在和用户进行一对一私聊", prompt)
        self.assertIn("不要每步都点评", prompt)

    @patch(
        "apps.games.services.LLMClient.generate",
        return_value='{"speak": false, "content": ""}',
    )
    def test_ordinary_move_can_stay_silent(self, _generate):
        board = [[0 for _ in range(15)] for _ in range(15)]
        board[7][7] = 1

        response = self.client.post(
            "/api/games/gomoku/respond/",
            {
                "persona_id": self.persona.id,
                "board": board,
                "history": [],
                "message": "用户刚刚落在 H8。",
                "action": "move",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["reply"], "")
        self.assertIsNotNone(response.data["ai_move"])

    @patch(
        "apps.games.services.LLMClient.generate",
        return_value="先不告诉你。",
    )
    def test_chat_prompt_keeps_future_move_secret(self, generate):
        board = [[0 for _ in range(15)] for _ in range(15)]

        response = self.client.post(
            "/api/games/gomoku/respond/",
            {
                "persona_id": self.persona.id,
                "board": board,
                "history": [
                    {
                        "role": "user",
                        "content": "你下一步打算下在哪里？",
                    }
                ],
                "message": "你下一步打算下在哪里？",
                "action": "chat",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["reply"], "先不告诉你。")
        prompt = generate.call_args.args[0]
        self.assertIn("落子计划保密规则", prompt)
        self.assertIn("绝对不要透露尚未落下的棋", prompt)
        self.assertIn("即使用户换一种问法", prompt)

    def test_hidden_persona_cannot_be_used(self):
        private_persona = Persona.objects.create(
            name="别人的人格",
            owner=get_user_model().objects.create_user(username="other-player"),
        )
        board = [[0 for _ in range(15)] for _ in range(15)]

        response = self.client.post(
            "/api/games/gomoku/respond/",
            {
                "persona_id": private_persona.id,
                "board": board,
                "action": "chat",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)
