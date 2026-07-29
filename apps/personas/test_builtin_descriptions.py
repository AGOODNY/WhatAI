from django.test import SimpleTestCase

from .builtin_descriptions import BUILTIN_DESCRIPTIONS
from .models import Persona
from .serializers import PersonaSerializer


class BuiltinDescriptionTests(SimpleTestCase):
    def test_all_builtin_descriptions_are_chinese(self):
        self.assertEqual(set(BUILTIN_DESCRIPTIONS), {"A", "B", "C", "D"})
        for legacy_role, description in BUILTIN_DESCRIPTIONS.items():
            self.assertRegex(description, r"[\u3400-\u9fff]")
            self.assertNotRegex(description, r"[A-Za-z]")

            persona = Persona(
                name=legacy_role,
                legacy_role=legacy_role,
                is_builtin=True,
                description="English fallback",
            )
            self.assertEqual(
                PersonaSerializer(persona).data["description"],
                description,
            )

