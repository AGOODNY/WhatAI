from types import SimpleNamespace
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.test import APIClient

from apps.chat.models import ChatRoom
from apps.dialogue.services.llm_client import LLMClient
from apps.personas.models import Persona
from apps.private_chat.models import PrivateChatRoom
from apps.private_chat.services.ai_reply_service import generate_ai_replies
from apps.users.services.model_selection import get_user_llm_model
from apps.worker.tasks import run_one_step_for_room
from config.llm_models import AVAILABLE_LLM_MODELS


class ModelPreferenceApiTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="model-user", password="password")
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_profile_exposes_default_and_available_models(self):
        response = self.client.get("/api/users/me/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["llm_model"], "deepseek-v4-flash")
        self.assertEqual(response.data["available_llm_models"], list(AVAILABLE_LLM_MODELS))

    def test_profile_can_switch_model(self):
        response = self.client.post(
            "/api/users/profile/update/",
            {"nickname": "tester", "llm_model": "deepseek-v4-pro"},
            format="multipart",
        )

        self.assertEqual(response.status_code, 200)
        self.user.profile.refresh_from_db()
        self.assertEqual(self.user.profile.llm_model, "deepseek-v4-pro")
        self.assertEqual(get_user_llm_model(self.user), "deepseek-v4-pro")

    def test_profile_rejects_unsupported_model(self):
        response = self.client.post(
            "/api/users/profile/update/",
            {"llm_model": "unknown-model"},
            format="multipart",
        )

        self.assertEqual(response.status_code, 400)
        self.user.profile.refresh_from_db()
        self.assertEqual(self.user.profile.llm_model, "deepseek-v4-flash")


class ModelSelectionPropagationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="chat-model-user", password="password")
        self.user.profile.llm_model = "deepseek-v4-flash"
        self.user.profile.save(update_fields=["llm_model"])
        self.persona = Persona.objects.filter(is_builtin=True).first()

    @patch("apps.worker.tasks.MessageService.create_messages")
    @patch("apps.worker.tasks.generate_group_messages")
    @patch("apps.worker.tasks.choose_next_speaker")
    @patch("apps.worker.tasks.get_history", return_value=[])
    def test_group_chat_uses_room_owner_model(
        self,
        get_history,
        choose_next_speaker,
        generate_group_messages,
        create_messages,
    ):
        room = ChatRoom.objects.create(
            owner=self.user,
            name="model room",
            scenario="普通闲聊",
        )
        room.personas.add(self.persona)
        choose_next_speaker.return_value = str(self.persona.id)
        generate_group_messages.return_value = ["好"]
        create_messages.return_value = [SimpleNamespace(id=1)]

        run_one_step_for_room(room)

        self.assertEqual(
            generate_group_messages.call_args.kwargs["model"],
            "deepseek-v4-flash",
        )

    @patch("apps.private_chat.services.ai_reply_service.generate_private_messages")
    def test_private_chat_uses_room_user_model(self, generate_private_messages):
        room = PrivateChatRoom.objects.create(
            user=self.user,
            ai_role=self.persona.legacy_role,
            persona=self.persona,
            title="private",
        )
        generate_private_messages.return_value = []

        generate_ai_replies(room)

        self.assertEqual(
            generate_private_messages.call_args.kwargs["model"],
            "deepseek-v4-flash",
        )


class LLMClientModelTests(TestCase):
    @patch("apps.dialogue.services.llm_client.OpenAI")
    def test_selected_model_is_sent_to_deepseek(self, openai):
        create = openai.return_value.chat.completions.create
        create.return_value = SimpleNamespace(
            choices=[
                SimpleNamespace(
                    message=SimpleNamespace(content="ok"),
                )
            ],
        )
        client = LLMClient(api_key="test-key")

        result = client.generate("hello", model="deepseek-v4-pro")

        self.assertEqual(result, "ok")
        self.assertEqual(create.call_args.kwargs["model"], "deepseek-v4-pro")
        self.assertEqual(
            create.call_args.kwargs["extra_body"],
            {"thinking": {"type": "disabled"}},
        )
        self.assertEqual(
            create.call_args.kwargs["messages"][0]["role"],
            "system",
        )
        self.assertIn(
            "禁止输出动作",
            create.call_args.kwargs["messages"][0]["content"],
        )

    @patch("apps.dialogue.services.llm_client.OpenAI")
    def test_action_descriptions_are_removed_from_all_outputs(self, openai):
        create = openai.return_value.chat.completions.create
        create.return_value = SimpleNamespace(
            choices=[
                SimpleNamespace(
                    message=SimpleNamespace(
                        content="（笑了一下）你好 *挥手*",
                    ),
                )
            ],
        )
        client = LLMClient(api_key="test-key")

        result = client.generate("hello", model="deepseek-v4-flash")

        self.assertEqual(result, "你好")

    @patch("apps.dialogue.services.llm_client.OpenAI")
    def test_failed_selected_model_does_not_silently_switch(self, openai):
        create = openai.return_value.chat.completions.create
        create.side_effect = RuntimeError("request failed")
        client = LLMClient(api_key="test-key")

        result = client.generate("hello", model="deepseek-v4-flash")

        self.assertEqual(result, "（模型调用失败：deepseek-v4-flash）")
        self.assertEqual(create.call_count, 1)
        self.assertEqual(create.call_args.kwargs["model"], "deepseek-v4-flash")
