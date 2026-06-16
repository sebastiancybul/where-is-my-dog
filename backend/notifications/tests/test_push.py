from types import SimpleNamespace
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from firebase_admin import messaging

from notifications import push
from notifications.models import DeviceToken

User = get_user_model()


class SendToUserTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="u1", email="u1@example.com", password="pass12345"
        )

    @patch("notifications.push.messaging.send_each_for_multicast")
    @patch("notifications.push._ensure_app")
    def test_returns_zero_and_skips_firebase_without_tokens(
        self, mock_ensure, mock_send
    ):
        result = push.send_to_user(
            user_id=self.user.id,
            event_type="location_reported",
            title="t",
            body="b",
        )

        self.assertEqual(result, 0)
        mock_ensure.assert_not_called()
        mock_send.assert_not_called()

    @patch("notifications.push.messaging.send_each_for_multicast")
    @patch("notifications.push._ensure_app")
    def test_prunes_dead_tokens_and_keeps_live_ones(
        self, mock_ensure, mock_send
    ):
        DeviceToken.objects.create(
            user=self.user, token="tok-live", platform="android"
        )
        DeviceToken.objects.create(
            user=self.user, token="tok-dead", platform="android"
        )

        tokens = list(
            DeviceToken.objects.filter(user=self.user).values_list(
                "token", flat=True
            )
        )
        responses = [
            (
                SimpleNamespace(
                    success=False,
                    exception=messaging.UnregisteredError("dead token"),
                )
                if token == "tok-dead"
                else SimpleNamespace(success=True, exception=None)
            )
            for token in tokens
        ]
        mock_send.return_value = SimpleNamespace(
            success_count=sum(1 for r in responses if r.success),
            responses=responses,
        )

        result = push.send_to_user(
            user_id=self.user.id,
            event_type="location_reported",
            title="t",
            body="b",
        )

        self.assertEqual(result, 1)
        self.assertFalse(DeviceToken.objects.filter(token="tok-dead").exists())
        self.assertTrue(DeviceToken.objects.filter(token="tok-live").exists())

    @patch("notifications.push.messaging.send_each_for_multicast")
    @patch("notifications.push._ensure_app")
    def test_keeps_token_on_transient_failure(self, mock_ensure, mock_send):
        DeviceToken.objects.create(
            user=self.user, token="tok-1", platform="android"
        )

        mock_send.return_value = SimpleNamespace(
            success_count=0,
            responses=[
                SimpleNamespace(
                    success=False, exception=Exception("network blip")
                )
            ],
        )

        with self.assertLogs("notifications.push", level="WARNING"):
            result = push.send_to_user(
                user_id=self.user.id,
                event_type="location_reported",
                title="t",
                body="b",
            )

        self.assertEqual(result, 0)
        self.assertTrue(DeviceToken.objects.filter(token="tok-1").exists())
