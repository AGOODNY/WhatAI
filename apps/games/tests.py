from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import SimpleTestCase
from rest_framework.test import APITestCase

from apps.personas.models import Persona

from .idiom_data import IDIOMS
from .idiom_services import (
    create_game_token,
    same_syllable_and_tone,
    validate_submission,
)
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


class IdiomServiceTests(SimpleTestCase):
    def test_same_syllable_requires_same_tone(self):
        self.assertTrue(same_syllable_and_tone("li4", "li4"))
        self.assertFalse(same_syllable_and_tone("li4", "li2"))

    def test_homophone_with_same_tone_is_accepted(self):
        chain = [{"word": "自不量力", "player": "ai"}]

        accepted, reason = validate_submission("丽句清词", chain)

        self.assertTrue(accepted)
        self.assertEqual(reason, "")

    def test_homophone_with_different_tone_is_rejected(self):
        chain = [{"word": "自不量力", "player": "ai"}]

        accepted, reason = validate_submission("离经叛道", chain)

        self.assertFalse(accepted)
        self.assertIn("不是同音同调", reason)

    def test_non_chinese_four_character_input_is_rejected(self):
        chain = [{"word": "自不量力", "player": "ai"}]

        accepted, reason = validate_submission("abcd", chain)

        self.assertFalse(accepted)
        self.assertEqual(reason, "请输入一个四字成语。")


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
        return_value='{"speak": true, "content": "这盘得认真点了。"}',
    )
    def test_forced_cadence_move_must_reply(self, generate):
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
                "force_reply": True,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["reply"], "这盘得认真点了。")
        prompt = generate.call_args.args[0]
        self.assertIn("距离你上次开口已经下了 4-7 枚棋", prompt)
        self.assertIn("本轮必须开口", prompt)

    @patch(
        "apps.games.services.LLMClient.generate",
        return_value='{"speak": false, "content": ""}',
    )
    def test_forced_cadence_has_nonempty_fallback(self, _generate):
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
                "force_reply": True,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["reply"])

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


class IdiomApiTests(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="idiom-player",
            password="test-password",
        )
        self.persona = Persona.objects.create(
            name="接龙搭档",
            description="喜欢文字游戏",
            is_builtin=True,
        )
        self.client.force_authenticate(self.user)

    @patch(
        "apps.games.idiom_services.LLMClient.generate",
        return_value="一心一意，接得上就来。",
    )
    def test_start_returns_opening_and_timer(self, _generate):
        response = self.client.post(
            "/api/games/idiom/start/",
            {"persona_id": self.persona.id},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn(response.data["chain"][0]["word"], IDIOMS)
        self.assertEqual(response.data["chain"][0]["player"], "ai")
        self.assertEqual(response.data["turn"], "user")
        self.assertEqual(response.data["seconds"], 60)
        self.assertTrue(response.data["game_token"])

    @patch(
        "apps.games.idiom_services.LLMClient.generate",
        return_value="这条规矩还算简单。",
    )
    def test_chat_reuses_private_prompt_and_knows_tone_rule(self, generate):
        token = create_game_token(self.user, self.persona, "自不量力")
        response = self.client.post(
            "/api/games/idiom/respond/",
            {
                "persona_id": self.persona.id,
                "game_token": token,
                "chain": [{"word": "自不量力", "player": "ai"}],
                "history": [{"role": "user", "content": "规则是什么？"}],
                "action": "chat",
                "message": "规则是什么？",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        prompt = generate.call_args.args[0]
        self.assertIn("你正在和用户进行一对一私聊", prompt)
        self.assertIn("“力”lì 可以接“丽”lì", prompt)
        self.assertIn("不能接“离”lí", prompt)
        self.assertIn("按你当前的人格自然回答", prompt)

    @patch(
        "apps.games.idiom_services.LLMClient.generate",
        return_value="接得不错。",
    )
    def test_valid_homophone_submission_gets_ai_idiom(self, _generate):
        token = create_game_token(self.user, self.persona, "自不量力")
        response = self.client.post(
            "/api/games/idiom/respond/",
            {
                "persona_id": self.persona.id,
                "game_token": token,
                "chain": [{"word": "自不量力", "player": "ai"}],
                "history": [],
                "action": "submit",
                "message": "丽句清词",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["accepted"])
        self.assertEqual(response.data["user_word"], "丽句清词")
        ai_word = response.data["ai_word"]
        if ai_word:
            self.assertEqual(IDIOMS[ai_word]["first"], IDIOMS["丽句清词"]["last"])
            self.assertIn(ai_word, response.data["reply"])

    @patch(
        "apps.games.idiom_services.LLMClient.generate",
        return_value="声调不对，再想想。",
    )
    def test_different_tone_submission_is_not_added(self, _generate):
        token = create_game_token(self.user, self.persona, "自不量力")
        response = self.client.post(
            "/api/games/idiom/respond/",
            {
                "persona_id": self.persona.id,
                "game_token": token,
                "chain": [{"word": "自不量力", "player": "ai"}],
                "history": [],
                "action": "submit",
                "message": "离经叛道",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.data["accepted"])
        self.assertIn("不是同音同调", response.data["error"])

    @patch("apps.games.idiom_services.LLMClient.generate")
    def test_unknown_valid_idiom_is_judged_and_signed_into_game_token(self, generate):
        generate.side_effect = [
            (
                '{"valid": true, "first": "feng1", "last": "li4", '
                '"reason": ""}'
            ),
            "接得可以，我也来一个。",
            "当然还没结束。",
        ]
        token = create_game_token(self.user, self.persona, "空穴来风")
        response = self.client.post(
            "/api/games/idiom/respond/",
            {
                "persona_id": self.persona.id,
                "game_token": token,
                "chain": [{"word": "空穴来风", "player": "ai"}],
                "history": [],
                "action": "submit",
                "message": "风声鹤唳",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["accepted"])
        self.assertEqual(response.data["user_word"], "风声鹤唳")
        self.assertTrue(response.data["game_token"])
        self.assertIsNotNone(response.data["ai_word"])
        self.assertEqual(
            IDIOMS[response.data["ai_word"]]["first"],
            "li4",
        )
        judge_call = generate.call_args_list[0]
        self.assertIn("严格的现代汉语成语词典校验器", judge_call.args[0])
        self.assertEqual(judge_call.kwargs["temperature"], 0.0)

        continued_chain = [
            {"word": "空穴来风", "player": "ai"},
            {"word": "风声鹤唳", "player": "user"},
            {"word": response.data["ai_word"], "player": "ai"},
        ]
        continued = self.client.post(
            "/api/games/idiom/respond/",
            {
                "persona_id": self.persona.id,
                "game_token": response.data["game_token"],
                "chain": continued_chain,
                "history": [],
                "action": "chat",
                "message": "还没结束吧？",
            },
            format="json",
        )

        self.assertEqual(continued.status_code, 200)
        self.assertEqual(continued.data["reply"], "当然还没结束。")

        rejected_old_token = self.client.post(
            "/api/games/idiom/respond/",
            {
                "persona_id": self.persona.id,
                "game_token": token,
                "chain": continued_chain,
                "history": [],
                "action": "chat",
                "message": "旧凭证不该接受动态词条",
            },
            format="json",
        )
        self.assertEqual(rejected_old_token.status_code, 400)

    @patch("apps.games.idiom_services.LLMClient.generate")
    def test_unknown_invalid_phrase_is_rejected_and_timer_resets(self, generate):
        generate.side_effect = [
            (
                '{"valid": false, "first": "", "last": "", '
                '"reason": "这是临时拼接的四字短语"}'
            ),
            "这个不算成语，换一个。",
        ]
        token = create_game_token(self.user, self.persona, "空穴来风")
        response = self.client.post(
            "/api/games/idiom/respond/",
            {
                "persona_id": self.persona.id,
                "game_token": token,
                "chain": [{"word": "空穴来风", "player": "ai"}],
                "history": [],
                "action": "submit",
                "message": "风来水转",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.data["accepted"])
        self.assertTrue(response.data["reset_timer"])
        self.assertIn("临时拼接", response.data["error"])

    @patch("apps.games.idiom_services.LLMClient.generate")
    def test_unknown_idiom_with_wrong_tone_is_rejected(self, generate):
        generate.side_effect = [
            (
                '{"valid": true, "first": "feng4", "last": "li4", '
                '"reason": ""}'
            ),
            "声调不对。",
        ]
        token = create_game_token(self.user, self.persona, "空穴来风")
        response = self.client.post(
            "/api/games/idiom/respond/",
            {
                "persona_id": self.persona.id,
                "game_token": token,
                "chain": [{"word": "空穴来风", "player": "ai"}],
                "history": [],
                "action": "submit",
                "message": "风来水转",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.data["accepted"])
        self.assertIn("不是同音同调", response.data["error"])
