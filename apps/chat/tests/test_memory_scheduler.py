from datetime import timedelta
from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone

from apps.memory.services.memory_manager import MemoryManager
from apps.personas.models import Persona
from apps.scheduler.services.scheduler import choose_next_speaker
from apps.worker.tasks import _conversation_energy, _next_delay_seconds


def _messages(count, role="USER"):
    return [
        {
            "id": index,
            "role": role,
            "content": f"消息{index}",
        }
        for index in range(1, count + 1)
    ]


class MemoryManagerTests(TestCase):
    def setUp(self):
        MemoryManager.clear_cache()

    @patch("apps.memory.services.memory_manager.llm_client.generate")
    def test_summary_refreshes_in_batches(self, generate):
        generate.side_effect = ["第一次摘要", "第二次摘要"]

        first = MemoryManager.build_context(
            _messages(35),
            conversation_key=1,
            mode="private",
            persona_name="Catpernicus",
            model_name="deepseek-v4-pro",
        )
        second = MemoryManager.build_context(
            _messages(40),
            conversation_key=1,
            mode="private",
            persona_name="Catpernicus",
            model_name="deepseek-v4-pro",
        )
        third = MemoryManager.build_context(
            _messages(45),
            conversation_key=1,
            mode="private",
            persona_name="Catpernicus",
            model_name="deepseek-v4-pro",
        )

        self.assertEqual(first[0]["content"], "第一次摘要")
        self.assertEqual(second[0]["content"], "第一次摘要")
        self.assertEqual(third[0]["content"], "第二次摘要")
        self.assertEqual(generate.call_count, 2)
        self.assertIn("一对一私聊", generate.call_args_list[0].args[0])
        self.assertNotIn("多人群聊", generate.call_args_list[0].args[0])
        self.assertEqual(
            generate.call_args_list[0].kwargs["model"],
            "deepseek-v4-pro",
        )


class SchedulerTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.personas = list(Persona.objects.filter(is_builtin=True).order_by("legacy_role"))

    def _captured_weights(self, history, last_role):
        roles = [str(persona.id) for persona in self.personas]
        with patch("apps.scheduler.services.scheduler.random.choices") as choices:
            choices.return_value = [roles[0]]
            choose_next_speaker(
                history,
                last_role,
                roles,
                personas=self.personas,
            )
        return dict(zip(choices.call_args.args[0], choices.call_args.kwargs["weights"]))

    def test_last_speaker_is_cooled_down(self):
        cat = next(item for item in self.personas if item.legacy_role == "A")
        weights = self._captured_weights([], str(cat.id))
        self.assertLess(weights[str(cat.id)], 0.1)

    def test_name_mention_boosts_that_persona(self):
        cat = next(item for item in self.personas if item.legacy_role == "A")
        pigeon = next(item for item in self.personas if item.legacy_role == "D")
        plain = self._captured_weights(
            [{"role": str(cat.id), "content": "这个怎么回事"}],
            str(cat.id),
        )
        mentioned = self._captured_weights(
            [{"role": str(cat.id), "content": "Pigeon 你觉得呢"}],
            str(cat.id),
        )
        self.assertGreater(mentioned[str(pigeon.id)], plain[str(pigeon.id)] * 2)

    def test_quoting_an_ai_strongly_boosts_that_persona(self):
        pigeon = next(item for item in self.personas if item.legacy_role == "D")
        plain = self._captured_weights(
            [{"role": "user", "content": "我接着说"}],
            str(pigeon.id),
        )
        quoted = self._captured_weights(
            [{
                "role": "user",
                "content": "我接着说",
                "reply_to_role": str(pigeon.id),
            }],
            str(pigeon.id),
        )
        self.assertGreater(
            quoted[str(pigeon.id)],
            plain[str(pigeon.id)] * 6,
        )

    def test_energy_uses_questions_and_recent_activity(self):
        now = timezone.now()
        history = [
            {
                "role": "A",
                "content": "这个是真的吗？",
                "timestamp": now - timedelta(seconds=2),
            }
        ]
        self.assertEqual(_conversation_energy(history), "hot")

        with patch("apps.worker.tasks.random.uniform", return_value=3.0), patch(
            "apps.worker.tasks.random.random", return_value=1.0
        ):
            self.assertEqual(_next_delay_seconds(history), 3.0)
