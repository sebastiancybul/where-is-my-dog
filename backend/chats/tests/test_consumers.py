from unittest.mock import patch

from asgiref.sync import async_to_sync
from channels.testing import WebsocketCommunicator
from django.contrib.auth import get_user_model
from django.test import TransactionTestCase, override_settings

from chats.models import Conversation, ConversationMembership
from config.asgi import application

User = get_user_model()

CHANNEL_LAYERS_OVERRIDE = {
    "default": {"BACKEND": "channels.layers.InMemoryChannelLayer"}
}


def ws_url(conversation_id, ticket="test_ticket"):
    return f"/ws/chats/{conversation_id}/?ticket={ticket}"


@override_settings(CHANNEL_LAYERS=CHANNEL_LAYERS_OVERRIDE)
class ChatConsumerConnectTests(TransactionTestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="user1", email="user1@example.com", password="pass123"
        )
        self.other_user = User.objects.create_user(
            username="user2", email="user2@example.com", password="pass123"
        )
        self.conversation = Conversation.objects.create(type=Conversation.TYPE_PRIVATE)
        ConversationMembership.objects.create(user=self.user, conversation=self.conversation)

    def test_connect_with_valid_ticket(self):
        async def run():
            with patch("chats.middleware.consume_ticket", return_value=self.user.pk):
                communicator = WebsocketCommunicator(application, ws_url(self.conversation.pk))
                connected, _ = await communicator.connect()
                self.assertTrue(connected)
                await communicator.disconnect()
        async_to_sync(run)()

    def test_connect_with_invalid_ticket(self):
        async def run():
            with patch("chats.middleware.consume_ticket", return_value=None):
                communicator = WebsocketCommunicator(application, ws_url(self.conversation.pk))
                connected, _ = await communicator.connect()
                self.assertFalse(connected)
        async_to_sync(run)()

    def test_connect_as_non_member(self):
        async def run():
            with patch("chats.middleware.consume_ticket", return_value=self.other_user.pk):
                communicator = WebsocketCommunicator(application, ws_url(self.conversation.pk))
                connected, _ = await communicator.connect()
                self.assertFalse(connected)
        async_to_sync(run)()


@override_settings(CHANNEL_LAYERS=CHANNEL_LAYERS_OVERRIDE)
class ChatConsumerMessagingTests(TransactionTestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="user1", email="user1@example.com", password="pass123"
        )
        self.conversation = Conversation.objects.create(type=Conversation.TYPE_PRIVATE)
        ConversationMembership.objects.create(user=self.user, conversation=self.conversation)

    def test_send_valid_message(self):
        async def run():
            with patch("chats.middleware.consume_ticket", return_value=self.user.pk):
                communicator = WebsocketCommunicator(application, ws_url(self.conversation.pk))
                connected, _ = await communicator.connect()
                self.assertTrue(connected)

                await communicator.send_json_to({"type": "chat_message", "body": "Hello!"})
                response = await communicator.receive_json_from()

                self.assertEqual(response["type"], "chat_message")
                self.assertEqual(response["body"], "Hello!")
                await communicator.disconnect()
        async_to_sync(run)()

    def test_invalid_json_returns_error(self):
        async def run():
            with patch("chats.middleware.consume_ticket", return_value=self.user.pk):
                communicator = WebsocketCommunicator(application, ws_url(self.conversation.pk))
                connected, _ = await communicator.connect()

                await communicator.send_to(text_data="not valid json{{{")
                response = await communicator.receive_json_from()

                self.assertEqual(response["type"], "error")
                self.assertEqual(response["code"], "invalid_json")
                await communicator.disconnect()
        async_to_sync(run)()

    def test_message_too_long_returns_error(self):
        async def run():
            with patch("chats.middleware.consume_ticket", return_value=self.user.pk):
                communicator = WebsocketCommunicator(application, ws_url(self.conversation.pk))
                connected, _ = await communicator.connect()

                await communicator.send_json_to({"type": "chat_message", "body": "x" * 10_001})
                response = await communicator.receive_json_from()

                self.assertEqual(response["type"], "error")
                self.assertEqual(response["code"], "invalid_message")
                await communicator.disconnect()
        async_to_sync(run)()

    def test_send_message_to_closed_conversation(self):
        self.conversation.is_closed = True
        self.conversation.save()

        async def run():
            with patch("chats.middleware.consume_ticket", return_value=self.user.pk):
                communicator = WebsocketCommunicator(application, ws_url(self.conversation.pk))
                connected, _ = await communicator.connect()

                await communicator.send_json_to({"type": "chat_message", "body": "Hello!"})
                response = await communicator.receive_json_from()

                self.assertEqual(response["type"], "error")
                self.assertEqual(response["code"], "conversation_closed")
                await communicator.disconnect()
        async_to_sync(run)()


@override_settings(CHANNEL_LAYERS=CHANNEL_LAYERS_OVERRIDE)
class ChatConsumerEdgeCaseTests(TransactionTestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="user1", email="user1@example.com", password="pass123"
        )

    def test_connect_to_nonexistent_conversation(self):
        async def run():
            with patch("chats.middleware.consume_ticket", return_value=self.user.pk):
                communicator = WebsocketCommunicator(application, ws_url(99999))
                connected, _ = await communicator.connect()
                self.assertFalse(connected)
        async_to_sync(run)()