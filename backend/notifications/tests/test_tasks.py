from unittest.mock import patch

from django.test import SimpleTestCase

from notifications.tasks import send_push_to_user


class SendPushToUserTaskTests(SimpleTestCase):
    @patch("notifications.tasks.push.send_to_user")
    @patch("notifications.tasks.presence.is_online")
    def test_skips_push_when_user_online(self, mock_is_online, mock_send):
        mock_is_online.return_value = True

        result = send_push_to_user(
            user_id=1,
            event_type="new_message",
            title="Sender",
            body="hi",
            data={"conversation_id": 5},
        )

        self.assertIsNone(result)
        mock_send.assert_not_called()

    @patch("notifications.tasks.push.send_to_user")
    @patch("notifications.tasks.presence.is_online")
    def test_sends_push_when_user_offline(self, mock_is_online, mock_send):
        mock_is_online.return_value = False
        mock_send.return_value = 1

        result = send_push_to_user(
            user_id=1,
            event_type="new_message",
            title="Sender",
            body="hi",
            data={"conversation_id": 5},
        )

        self.assertEqual(result, 1)
        mock_send.assert_called_once_with(
            user_id=1,
            event_type="new_message",
            title="Sender",
            body="hi",
            data={"conversation_id": 5},
        )
