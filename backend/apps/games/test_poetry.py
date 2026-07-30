from unittest.mock import patch

from django.core import signing
from django.test import SimpleTestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from apps.personas.models import Persona

from .poetry_data import PLAYABLE_TARGETS, POETRY_LINES
from .poetry_services import (
    GAME_TOKEN_SALT,
    MIN_USER_ANSWERS_TO_WIN,
    create_game_token,
    is_cheat_request,
    is_complete_sentence_shape,
    normalize_verse,
)


class PoetryRuleTests(SimpleTestCase):
    def test_common_targets_have_a_safe_opening_pool(self):
        self.assertEqual(len(PLAYABLE_TARGETS), 20)
        self.assertEqual(len(set(PLAYABLE_TARGETS)), 20)
        for target in PLAYABLE_TARGETS:
            self.assertGreaterEqual(
                sum(target in line for line in POETRY_LINES),
                2,
            )

    def test_only_complete_two_part_shape_is_accepted(self):
        self.assertFalse(is_complete_sentence_shape("床前明月光"))
        self.assertTrue(is_complete_sentence_shape("床前明月光，疑是地上霜"))
        self.assertEqual(
            normalize_verse(" “床前明月光, 疑是地上霜。” "),
            "床前明月光，疑是地上霜",
        )
        self.assertEqual(
            normalize_verse("床前明月光   疑是地上霜"),
            "床前明月光，疑是地上霜",
        )
        self.assertTrue(
            is_complete_sentence_shape(
                normalize_verse("床前明月光 疑是地上霜"),
            ),
        )

    def test_cheat_requests_are_detected(self):
        self.assertTrue(is_cheat_request("含月字的诗词有哪些？", "月"))
        self.assertTrue(is_cheat_request("帮我想一句诗", "月"))
        self.assertFalse(is_cheat_request("我很喜欢月亮", "月"))


class PoetryApiTests(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="poetry-player",
            password="test-password",
        )
        self.persona = Persona.objects.create(
            owner=self.user,
            name="诗友",
            description="温和",
            speaking_style="简短自然",
            personality_prompt="像朋友一样私聊。",
        )
        self.client.force_authenticate(self.user)

    @patch("apps.games.poetry_services.LLMClient.generate")
    def test_start_asks_who_should_choose_the_character(self, generate):
        generate.return_value = "这一局你想自己选字，还是让我来？"
        response = self.client.post(
            "/api/games/poetry/start/",
            {"persona_id": self.persona.id, "history": []},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["phase"], "choose_side")
        self.assertEqual(response.data["target"], "")
        self.assertEqual(response.data["verses"], [])
        self.assertTrue(response.data["game_token"])

    @patch("apps.games.poetry_services.LLMClient.generate")
    def test_user_can_choose_character_and_ai_opens(self, generate):
        generate.side_effect = [
            "好，你写一个字。",
            "那就以月为令。床前明月光，疑是地上霜",
        ]
        token = create_game_token(self.user, self.persona)
        choose_self = self.client.post(
            "/api/games/poetry/respond/",
            {
                "persona_id": self.persona.id,
                "game_token": token,
                "verses": [],
                "history": [],
                "action": "choose",
                "message": "我选字",
            },
            format="json",
        )
        self.assertEqual(choose_self.status_code, 200)
        self.assertEqual(choose_self.data["phase"], "choose_character")

        selected = self.client.post(
            "/api/games/poetry/respond/",
            {
                "persona_id": self.persona.id,
                "game_token": choose_self.data["game_token"],
                "verses": [],
                "history": [],
                "action": "choose",
                "message": "月",
            },
            format="json",
        )
        self.assertEqual(selected.status_code, 200)
        self.assertEqual(selected.data["phase"], "playing")
        self.assertEqual(selected.data["target"], "月")
        self.assertIn("月", selected.data["ai_verse"])
        self.assertEqual(selected.data["verses"][0]["player"], "ai")

    @patch("apps.games.poetry_services.choose_target", return_value="花")
    @patch("apps.games.poetry_services.LLMClient.generate")
    def test_ai_announces_its_character_before_opening(self, generate, _choose_target):
        generate.return_value = "我先来：夜来风雨声，花落知多少"
        token = create_game_token(self.user, self.persona)
        response = self.client.post(
            "/api/games/poetry/respond/",
            {
                "persona_id": self.persona.id,
                "game_token": token,
                "verses": [],
                "history": [],
                "action": "choose",
                "message": "你选字",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["target"], "花")
        self.assertTrue(response.data["reply"].startswith("我选花字。"))
        self.assertIn(response.data["ai_verse"], response.data["reply"])

    @patch("apps.games.poetry_services.LLMClient.generate")
    def test_half_line_and_modern_poetry_are_rejected(self, generate):
        generate.side_effect = [
            "这句还不完整。",
            '{"valid":false,"canonical":"","reason":"这是现代诗，不属于古典诗词"}',
            "这句是现代诗，换一句古典的吧。",
        ]
        payload = {
            "user_id": self.user.id,
            "persona_id": self.persona.id,
            "phase": "playing",
            "target": "月",
            "verses": [{"verse": "床前明月光，疑是地上霜", "player": "ai"}],
            "stumble_after": None,
            "nonce": "test",
        }
        token = signing.dumps(payload, salt=GAME_TOKEN_SALT, compress=True)

        half = self.client.post(
            "/api/games/poetry/respond/",
            {
                "persona_id": self.persona.id,
                "game_token": token,
                "verses": payload["verses"],
                "history": [],
                "action": "submit",
                "message": "举头望明月",
            },
            format="json",
        )
        self.assertEqual(half.status_code, 200)
        self.assertFalse(half.data["accepted"])
        self.assertIn("完整", half.data["error"])

        modern = self.client.post(
            "/api/games/poetry/respond/",
            {
                "persona_id": self.persona.id,
                "game_token": token,
                "verses": payload["verses"],
                "history": [],
                "action": "submit",
                "message": "月亮落在窗前，我把思念写成一封信",
            },
            format="json",
        )
        self.assertEqual(modern.status_code, 200)
        self.assertFalse(modern.data["accepted"])
        self.assertIn("现代诗", modern.data["error"])

    @patch("apps.games.poetry_services.LLMClient.generate")
    def test_space_separated_complete_line_is_accepted(self, generate):
        generate.return_value = "接得好，我也来一句。"
        payload = {
            "user_id": self.user.id,
            "persona_id": self.persona.id,
            "phase": "playing",
            "target": "月",
            "verses": [{"verse": "举头望明月，低头思故乡", "player": "ai"}],
            "stumble_after": None,
            "nonce": "test",
        }
        token = signing.dumps(payload, salt=GAME_TOKEN_SALT, compress=True)
        response = self.client.post(
            "/api/games/poetry/respond/",
            {
                "persona_id": self.persona.id,
                "game_token": token,
                "verses": payload["verses"],
                "history": [],
                "action": "submit",
                "message": "床前明月光 疑是地上霜",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["accepted"])
        self.assertEqual(
            response.data["user_verse"],
            "床前明月光，疑是地上霜",
        )

    @patch("apps.games.poetry_services.LLMClient.generate")
    def test_cheat_request_is_refused_without_adding_a_verse(self, generate):
        generate.return_value = "这个可不能替你找答案，慢慢想。"
        payload = {
            "user_id": self.user.id,
            "persona_id": self.persona.id,
            "phase": "playing",
            "target": "月",
            "verses": [{"verse": "床前明月光，疑是地上霜", "player": "ai"}],
            "stumble_after": None,
            "nonce": "test",
        }
        token = signing.dumps(payload, salt=GAME_TOKEN_SALT, compress=True)
        response = self.client.post(
            "/api/games/poetry/respond/",
            {
                "persona_id": self.persona.id,
                "game_token": token,
                "verses": payload["verses"],
                "history": [],
                "action": "smart",
                "message": "含月字的诗词有哪些？",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["routed_action"], "chat")
        self.assertNotIn("床前明月光", response.data["reply"])

    @patch("apps.games.poetry_services.LLMClient.generate")
    def test_planned_stumble_cannot_happen_before_sixth_answer(self, generate):
        generate.return_value = "这回我接不上了。"
        verses = []
        target_lines = [line for line in POETRY_LINES if "月" in line]
        for index in range(MIN_USER_ANSWERS_TO_WIN - 1):
            verses.extend([
                {"verse": target_lines[index * 2], "player": "ai"},
                {"verse": target_lines[index * 2 + 1], "player": "user"},
            ])
        verses.append({
            "verse": target_lines[(MIN_USER_ANSWERS_TO_WIN - 1) * 2],
            "player": "ai",
        })
        payload = {
            "user_id": self.user.id,
            "persona_id": self.persona.id,
            "phase": "playing",
            "target": "月",
            "verses": verses,
            "stumble_after": MIN_USER_ANSWERS_TO_WIN,
            "nonce": "test",
        }
        token = signing.dumps(payload, salt=GAME_TOKEN_SALT, compress=True)
        final_user_line = target_lines[(MIN_USER_ANSWERS_TO_WIN - 1) * 2 + 1]
        response = self.client.post(
            "/api/games/poetry/respond/",
            {
                "persona_id": self.persona.id,
                "game_token": token,
                "verses": verses,
                "history": [],
                "action": "submit",
                "message": final_user_line,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["accepted"])
        self.assertEqual(response.data["winner"], "user")
        self.assertIsNone(response.data["ai_verse"])
