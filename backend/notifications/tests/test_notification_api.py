from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from notifications.models import Notification

User = get_user_model()


def create_user(**params):
    defaults = {
        "username": "u1",
        "email": "u1@example.com",
        "password": "testpass123",
    }
    defaults.update(params)
    return User.objects.create_user(**defaults)


class NotificationInboxTests(APITestCase):
    def setUp(self):
        self.user = create_user(username="u1", email="u1@example.com")
        self.other = create_user(username="u2", email="u2@example.com")
        self.list_url = reverse("notifications:notification-list")

    def _make(self, user, **kwargs):
        defaults = {
            "event_type": Notification.EVENT_LOCATION_REPORTED,
            "title": "t",
            "body": "b",
            "data": {},
        }
        defaults.update(kwargs)
        return Notification.objects.create(user=user, **defaults)

    def test_list_requires_authentication(self):
        res = self.client.get(self.list_url)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_returns_only_own_notifications(self):
        self._make(self.user, title="mine")
        self._make(self.other, title="theirs")
        self.client.force_authenticate(self.user)

        res = self.client.get(self.list_url)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["count"], 1)
        self.assertEqual(res.data["results"][0]["title"], "mine")

    def test_list_is_paginated(self):
        for i in range(7):
            self._make(self.user, title=f"n{i}")
        self.client.force_authenticate(self.user)

        res = self.client.get(self.list_url)

        self.assertEqual(res.data["count"], 7)
        self.assertEqual(len(res.data["results"]), 5)
        self.assertIsNotNone(res.data["next"])

    def test_read_marks_single_as_read(self):
        notification = self._make(self.user, is_read=False)
        self.client.force_authenticate(self.user)
        url = reverse(
            "notifications:notification-read", args=[notification.pk]
        )

        res = self.client.post(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        notification.refresh_from_db()
        self.assertTrue(notification.is_read)

    def test_read_other_users_notification_returns_404(self):
        notification = self._make(self.other, is_read=False)
        self.client.force_authenticate(self.user)
        url = reverse(
            "notifications:notification-read", args=[notification.pk]
        )

        res = self.client.post(url)

        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        notification.refresh_from_db()
        self.assertFalse(notification.is_read)

    def test_read_all_marks_only_own_unread(self):
        self._make(self.user, is_read=False)
        self._make(self.user, is_read=False)
        other = self._make(self.other, is_read=False)
        self.client.force_authenticate(self.user)
        url = reverse("notifications:notification-read-all")

        res = self.client.post(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(
            Notification.objects.filter(user=self.user, is_read=False).count(),
            0,
        )
        other.refresh_from_db()
        self.assertFalse(other.is_read)
