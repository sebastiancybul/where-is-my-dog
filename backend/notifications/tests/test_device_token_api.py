from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from notifications.models import DeviceToken

User = get_user_model()


def create_user(**params):
    defaults = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpass123",
    }
    defaults.update(params)
    return User.objects.create_user(**defaults)


class DeviceTokenApiTests(APITestCase):
    def setUp(self):
        self.user = create_user(username="u1", email="u1@example.com")
        self.other = create_user(username="u2", email="u2@example.com")
        self.url = reverse("notifications:device-token")

    def test_register_creates_token(self):
        self.client.force_authenticate(user=self.user)

        res = self.client.post(
            self.url, {"token": "tok-123", "platform": "android"}
        )

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        token = DeviceToken.objects.get(token="tok-123")
        self.assertEqual(token.user, self.user)
        self.assertEqual(token.platform, "android")

    def test_register_same_token_reassigns_user(self):
        DeviceToken.objects.create(
            user=self.user, token="tok-123", platform="android"
        )

        self.client.force_authenticate(user=self.other)
        res = self.client.post(
            self.url, {"token": "tok-123", "platform": "android"}
        )

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(DeviceToken.objects.count(), 1)
        self.assertEqual(
            DeviceToken.objects.get(token="tok-123").user, self.other
        )

    def test_register_requires_authentication(self):
        res = self.client.post(
            self.url, {"token": "tok-123", "platform": "android"}
        )

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertFalse(DeviceToken.objects.exists())

    def test_delete_removes_own_token(self):
        DeviceToken.objects.create(
            user=self.user, token="tok-123", platform="android"
        )

        self.client.force_authenticate(user=self.user)
        res = self.client.delete(self.url, {"token": "tok-123"})

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(DeviceToken.objects.filter(token="tok-123").exists())

    def test_delete_does_not_remove_other_users_token(self):
        DeviceToken.objects.create(
            user=self.user, token="tok-123", platform="android"
        )

        self.client.force_authenticate(user=self.other)
        res = self.client.delete(self.url, {"token": "tok-123"})

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertTrue(DeviceToken.objects.filter(token="tok-123").exists())
