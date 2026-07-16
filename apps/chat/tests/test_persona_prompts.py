from unittest.mock import patch

from django.test import TestCase

from apps.dialogue.services.dialogue_engine import (
    clean_reply,
    clean_reply_list,
    generate_group_messages,
    is_repetitive_reply,
)
from apps.dialogue.services.private_prompt_builder import build_private_prompt
from apps.dialogue.services.prompt_builder import build_prompt
from apps.personas.models import Persona
from apps.personas.services import get_persona_by_token


class PersonaPromptTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.personas = {
            persona.legacy_role: persona
            for persona in Persona.objects.filter(is_builtin=True)
        }

    def test_builtin_profile_is_merged_without_runtime_chat_history(self):
        profile = get_persona_by_token(self.personas["A"])

        self.assertEqual(profile["display_name"], "Catpernicus")
        self.assertEqual(profile["speaking_style"]["bubble_weights"], [0.61, 0.26, 0.13])
        self.assertTrue(profile["relationships"]["B"])
        self.assertNotIn("chat_history", str(profile))

    def test_group_prompt_only_includes_active_relationships(self):
        cat = self.personas["A"]
        wither = self.personas["B"]
        prompt = build_prompt(
            str(cat.id),
            [{"id": 1, "role": str(wither.id), "speaker": "Wither", "content": "这个能玩吗"}],
            "普通闲聊",
            participants=[cat, wither],
            target_bubbles=2,
        )

        self.assertIn("当前成员：Catpernicus、Wither", prompt)
        self.assertIn("和 Wither 常互相补充解释", prompt)
        self.assertNotIn("和 Pigeon 常是快速问答", prompt)
        self.assertIn("恰好发送 2 个气泡", prompt)
        self.assertIn("2-12 个中文字符", prompt)

    def test_private_prompt_uses_readable_roles_and_no_group_relationships(self):
        cat = self.personas["A"]
        prompt = build_private_prompt(
            str(cat.id),
            [
                {"id": 1, "role": "USER", "content": "今天有点累"},
                {"id": 2, "role": str(cat.id), "content": "那先休息一下"},
            ],
            multi_bubble=True,
        )

        self.assertIn("用户：今天有点累", prompt)
        self.assertIn("Catpernicus：那先休息一下", prompt)
        self.assertNotIn("群聊成员与关系", prompt)
        self.assertNotIn(f"{cat.id}：", prompt)
        self.assertIn("默认不要反问", prompt)
        self.assertIn("禁止用“你呢？”", prompt)
        self.assertIn("允许话题暂时结束", prompt)

    def test_short_reply_is_allowed_unless_recently_repeated(self):
        self.assertFalse(is_repetitive_reply("草", [{"content": "这也行"}]))
        self.assertTrue(is_repetitive_reply("草", [{"content": "草"}]))

    def test_chat_parentheses_are_kept_but_stage_actions_are_removed(self):
        self.assertEqual(clean_reply("哇真厉害（棒读）"), "哇真厉害（棒读）")
        self.assertEqual(clean_reply("（微笑）可以啊"), "可以啊")

    def test_reply_list_keeps_new_short_messages_and_removes_duplicates(self):
        replies = clean_reply_list(
            ["草", "草", "这个确实有点怪"],
            history=[{"content": "没错"}],
            max_items=3,
        )
        self.assertEqual(replies, ["草", "这个确实有点怪"])

    @patch("apps.dialogue.services.dialogue_engine.llm_client.generate")
    @patch("apps.dialogue.services.dialogue_engine.MemoryManager.build_context")
    def test_group_generation_parses_multiple_bubbles(self, build_context, generate):
        cat = self.personas["A"]
        build_context.return_value = [{"id": 1, "role": "X", "speaker": "X", "content": "真的吗"}]
        generate.return_value = '["确实", "但是有点怪"]'

        replies = generate_group_messages(
            str(cat.id),
            build_context.return_value,
            room_id=10,
            participants=[cat],
            target_bubbles=2,
            model="deepseek-v4-flash",
        )

        self.assertEqual(replies, ["确实", "但是有点怪"])
        self.assertEqual(generate.call_args.kwargs["max_tokens"], 120)
        self.assertEqual(generate.call_args.kwargs["model"], "deepseek-v4-flash")
