from unittest.mock import AsyncMock, patch

from django.contrib.auth import get_user_model
from django.test import TestCase

from notifications.dispatch import dispatch_notification
from notifications.models import Notification

User = get_user_model()


class DispatchNotificationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="u1", email="u1@example.com", password="pass12345"
        )

    @patch("notifications.dispatch.send_push_to_user.delay")
    @patch("notifications.dispatch.notify_user", new_callable=AsyncMock)
    @patch("notifications.dispatch.presence.is_online")
    def test_persists_notification(
        self, mock_is_online, mock_notify, mock_delay
    ):
        mock_is_online.return_value = False

        notification = dispatch_notification(
            user_id=self.user.id,
            event_type=Notification.EVENT_LOCATION_REPORTED,
            title="Burek",
            body="u2 reported a new location",
            data={"listing_id": 7},
        )

        saved = Notification.objects.get(pk=notification.pk)
        self.assertEqual(saved.user, self.user)
        self.assertEqual(
            saved.event_type, Notification.EVENT_LOCATION_REPORTED
        )
        self.assertEqual(saved.title, "Burek")
        self.assertEqual(saved.data, {"listing_id": 7})
        self.assertFalse(saved.is_read)

    @patch("notifications.dispatch.send_push_to_user.delay")
    @patch("notifications.dispatch.notify_user", new_callable=AsyncMock)
    @patch("notifications.dispatch.presence.is_online")
    def test_online_sends_websocket_not_push(
        self, mock_is_online, mock_notify, mock_delay
    ):
        mock_is_online.return_value = True

        dispatch_notification(
            user_id=self.user.id,
            event_type=Notification.EVENT_LISTING_INQUIRY,
            title="u2 . Burek",
            body="Someone contacted you about your listing",
            data={"conversation_id": 3},
        )

        mock_notify.assert_awaited_once()
        mock_delay.assert_not_called()

    @patch("notifications.dispatch.send_push_to_user.delay")
    @patch("notifications.dispatch.notify_user", new_callable=AsyncMock)
    @patch("notifications.dispatch.presence.is_online")
    def test_offline_enqueues_push_not_websocket(
        self, mock_is_online, mock_notify, mock_delay
    ):
        mock_is_online.return_value = False

        dispatch_notification(
            user_id=self.user.id,
            event_type=Notification.EVENT_LISTING_INQUIRY,
            title="u2 . Burek",
            body="Someone contacted you about your listing",
            data={"conversation_id": 3},
        )

        mock_notify.assert_not_awaited()
        mock_delay.assert_called_once_with(
            user_id=self.user.id,
            event_type=Notification.EVENT_LISTING_INQUIRY,
            title="u2 . Burek",
            body="Someone contacted you about your listing",
            data={"conversation_id": 3},
        )
