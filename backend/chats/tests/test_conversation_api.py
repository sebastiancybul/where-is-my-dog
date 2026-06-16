from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from listings.tests.test_listings_api import create_listing
from notifications.models import Notification

User = get_user_model()


def create_user(**params):
    defaults = {
        "username": "cu",
        "email": "cu@example.com",
        "password": "testpass123",
    }
    defaults.update(params)
    return User.objects.create_user(**defaults)


class ConversationInquiryNotificationTests(APITestCase):
    def setUp(self):
        self.owner = create_user(username="owner", email="owner@example.com")
        self.inquirer = create_user(
            username="inquirer", email="inquirer@example.com"
        )
        self.listing = create_listing(self.owner)
        self.url = reverse("conversation-list")

    @patch("chats.views.conversation.dispatch_notification")
    def test_new_conversation_notifies_listing_owner(self, mock_dispatch):
        self.client.force_authenticate(user=self.inquirer)

        res = self.client.post(
            self.url,
            {"user_id": self.owner.id, "listing_id": self.listing.id},
        )

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        mock_dispatch.assert_called_once()
        kwargs = mock_dispatch.call_args.kwargs
        self.assertEqual(kwargs["user_id"], self.owner.id)
        self.assertEqual(
            kwargs["event_type"], Notification.EVENT_LISTING_INQUIRY
        )
        self.assertEqual(kwargs["data"]["listing_id"], self.listing.id)
        self.assertIn("conversation_id", kwargs["data"])

    @patch("chats.views.conversation.dispatch_notification")
    def test_existing_conversation_does_not_notify(self, mock_dispatch):
        self.client.force_authenticate(user=self.inquirer)
        payload = {"user_id": self.owner.id, "listing_id": self.listing.id}

        first = self.client.post(self.url, payload)
        self.assertEqual(first.status_code, status.HTTP_201_CREATED)

        mock_dispatch.reset_mock()

        second = self.client.post(self.url, payload)
        self.assertEqual(second.status_code, status.HTTP_200_OK)
        mock_dispatch.assert_not_called()
