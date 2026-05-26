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


def ws_chats_url(conversation_id, ticket="test_ticket"):
    return f"/ws/chats/{conversation_id}/?ticket={ticket}"


def ws_notifications_url(ticket="test_ticket"):
    return f"/ws/notifications/?ticket={ticket}"


@override_settings(CHANNEL_LAYERS=CHANNEL_LAYERS_OVERRIDE)
class UserNotificationConsumerTests(TransactionTestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="user1", email="user1@example.com", password="pass123"
        )
        self.other_user = User.objects.create_user(
            username="user2", email="user2@example.com", password="pass123"
        )
        self.conversation = Conversation.objects.create(
            type=Conversation.TYPE_PRIVATE
        )
        ConversationMembership.objects.create(
            user=self.user, conversation=self.conversation
        )
        ConversationMembership.objects.create(
            user=self.other_user, conversation=self.conversation
        )

    def test_connect_with_valid_ticket(self):
        async def run():
            with patch(
                "chats.middleware.consume_ticket",
                return_value=self.user.pk
            ):
                communicator = WebsocketCommunicator(
                    application, ws_notifications_url()
                )
                connected, _ = await communicator.connect()
                self.assertTrue(connected)
                await communicator.disconnect()
        async_to_sync(run)()

    def test_connect_with_invalid_ticket(self):
        async def run():
            with patch("chats.middleware.consume_ticket", return_value=None):
                communicator = WebsocketCommunicator(
                    application, ws_notifications_url()
                )
                connected, _ = await communicator.connect()
                self.assertFalse(connected)
        async_to_sync(run)()

    def test_recives_new_message_notifiaction(self):
        async def run():
            with patch(
                "chats.middleware.consume_ticket",
                return_value=self.other_user.pk
            ):
                communicator1 = WebsocketCommunicator(
                    application,
                    ws_notifications_url()
                )
                connected, _ = await communicator1.connect()
                self.assertTrue(connected)

                with patch(
                    "chats.middleware.consume_ticket",
                    return_value=self.user.pk
                ):
                    communicator2 = WebsocketCommunicator(
                        application,
                        ws_chats_url(self.conversation.pk)
                    )
                    connected, _ = await communicator2.connect()
                    self.assertTrue(connected)

                    await communicator2.send_json_to(
                        {
                            "type": "chat_message",
                            "body": "Hello"
                        }
                    )

                response = await communicator1.receive_json_from()

                self.assertEqual(response["type"], "new_notification")
                self.assertEqual(response["event_type"], "new_message")
                self.assertEqual(
                    response["payload"]["conversation_id"],
                    self.conversation.pk
                )
                self.assertEqual(
                    response["payload"]["last_message"]["body"], "Hello"
                )
        async_to_sync(run)()
