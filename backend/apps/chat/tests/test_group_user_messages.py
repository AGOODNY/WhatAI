from django.contrib.auth.models import User
from rest_framework.test import APITestCase

from apps.chat.models import ChatRoom, Message
from apps.personas.models import Persona


class GroupUserMessageTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="owner", password="password")
        self.other_user = User.objects.create_user(username="other", password="password")
        self.personas = [
            Persona.objects.create(name=f"Persona {index}", is_builtin=True)
            for index in range(4)
        ]
        self.client.force_authenticate(self.user)

    def test_user_can_join_without_reducing_four_ai_limit(self):
        response = self.client.post(
            "/api/chat/rooms/create/",
            {
                "name": "Five participants",
                "scenario": "A group discussion",
                "persona_ids": [persona.id for persona in self.personas],
                "user_participates": True,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        room = ChatRoom.objects.get(id=response.data["id"])
        self.assertTrue(room.user_participates)
        self.assertEqual(room.personas.count(), 4)

    def test_participating_user_can_send_a_group_message(self):
        room = ChatRoom.objects.create(
            name="Interactive",
            scenario="Chat",
            owner=self.user,
            user_participates=True,
        )

        response = self.client.post(
            f"/api/chat/rooms/{room.id}/send/",
            {"content": "  大家好  "},
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        self.assertTrue(response.data["is_user"])
        self.assertEqual(response.data["content"], "大家好")
        message = Message.objects.get(id=response.data["id"])
        self.assertEqual(message.role, "user")
        self.assertIsNone(message.persona_id)

    def test_user_can_quote_an_ai_message_in_the_same_room(self):
        room = ChatRoom.objects.create(
            name="Interactive",
            scenario="Chat",
            owner=self.user,
            user_participates=True,
        )
        persona = self.personas[0]
        quoted = Message.objects.create(
            room=room,
            role=str(persona.id),
            persona=persona,
            content="你觉得这个方案怎么样？",
        )

        response = self.client.post(
            f"/api/chat/rooms/{room.id}/send/",
            {
                "content": "我觉得可以",
                "reply_to_id": quoted.id,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["reply_to"]["id"], quoted.id)
        self.assertEqual(response.data["reply_to"]["display_name"], persona.name)
        self.assertEqual(
            Message.objects.get(id=response.data["id"]).reply_to_id,
            quoted.id,
        )

    def test_user_cannot_quote_a_message_from_another_room(self):
        room = ChatRoom.objects.create(
            name="Interactive",
            scenario="Chat",
            owner=self.user,
            user_participates=True,
        )
        other_room = ChatRoom.objects.create(
            name="Other",
            scenario="Chat",
            owner=self.user,
            user_participates=True,
        )
        quoted = Message.objects.create(
            room=other_room,
            role="someone",
            content="not in this room",
        )

        response = self.client.post(
            f"/api/chat/rooms/{room.id}/send/",
            {"content": "reply", "reply_to_id": quoted.id},
            format="json",
        )

        self.assertEqual(response.status_code, 400)

    def test_user_cannot_send_while_room_generation_is_paused(self):
        room = ChatRoom.objects.create(
            name="Paused",
            scenario="Chat",
            owner=self.user,
            user_participates=True,
            is_active=False,
        )

        response = self.client.post(
            f"/api/chat/rooms/{room.id}/send/",
            {"content": "还能发吗"},
            format="json",
        )

        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.data["error"], "当前群聊已经暂停生成")
        self.assertFalse(Message.objects.filter(room=room).exists())

    def test_spectator_and_non_owner_cannot_send(self):
        spectator_room = ChatRoom.objects.create(
            name="Spectator",
            scenario="Chat",
            owner=self.user,
            user_participates=False,
        )
        response = self.client.post(
            f"/api/chat/rooms/{spectator_room.id}/send/",
            {"content": "hello"},
            format="json",
        )
        self.assertEqual(response.status_code, 403)

        interactive_room = ChatRoom.objects.create(
            name="Private owner",
            scenario="Chat",
            owner=self.user,
            user_participates=True,
        )
        self.client.force_authenticate(self.other_user)
        response = self.client.post(
            f"/api/chat/rooms/{interactive_room.id}/send/",
            {"content": "hello"},
            format="json",
        )
        self.assertEqual(response.status_code, 404)
