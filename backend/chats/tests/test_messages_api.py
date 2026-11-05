from datetime import timedelta

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from chats.models import Conversation, ConversationMembership, Message

User = get_user_model()

PAGE_SIZE = 30


def create_user(**params):
    defaults = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpass123",
    }
    defaults.update(params)
    return User.objects.create_user(**defaults)


def create_messages(conversation, sender, count):
    messages = Message.objects.bulk_create(
        Message(conversation=conversation, sender=sender, body=f"msg {i}")
        for i in range(count)
    )
    base = timezone.now() - timedelta(days=1)
    for i, message in enumerate(messages):
        Message.objects.filter(pk=message.pk).update(
            created_at=base + timedelta(minutes=i)
        )
    return messages


class MessagesApiTests(APITestCase):
    def setUp(self):
        self.user = create_user(username="u1", email="u1@example.com")
        self.other = create_user(username="u2", email="u2@example.com")
        self.conversation = Conversation.objects.create(
            type=Conversation.TYPE_PRIVATE
        )
        ConversationMembership.objects.create(
            user=self.user, conversation=self.conversation
        )
        ConversationMembership.objects.create(
            user=self.other, conversation=self.conversation
        )
        self.url = reverse(
            "conversation-messages", args=[self.conversation.pk]
        )

    def test_unauthenticated_returns_401(self):
        res = self.client.get(self.url)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_non_member_returns_404(self):
        outsider = create_user(username="u3", email="u3@example.com")
        create_messages(self.conversation, self.user, 3)
        self.client.force_authenticate(user=outsider)

        res = self.client.get(self.url)

        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_empty_conversation_returns_empty_page(self):
        self.client.force_authenticate(user=self.user)

        res = self.client.get(self.url)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["count"], 0)
        self.assertEqual(res.data["results"], [])
        self.assertIsNone(res.data["next"])

    def test_fewer_than_page_size_returns_all(self):
        create_messages(self.conversation, self.user, 12)
        self.client.force_authenticate(user=self.user)

        res = self.client.get(self.url)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["count"], 12)
        self.assertEqual(len(res.data["results"]), 12)
        self.assertIsNone(res.data["next"])
        self.assertIsNone(res.data["previous"])

    def test_exactly_page_size_fits_on_one_page(self):
        create_messages(self.conversation, self.user, PAGE_SIZE)
        self.client.force_authenticate(user=self.user)

        res = self.client.get(self.url)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data["results"]), PAGE_SIZE)
        self.assertIsNone(res.data["next"])

    def test_first_page_returns_page_size_and_next(self):
        create_messages(self.conversation, self.user, 45)
        self.client.force_authenticate(user=self.user)

        res = self.client.get(self.url)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["count"], 45)
        self.assertEqual(len(res.data["results"]), PAGE_SIZE)
        self.assertIsNotNone(res.data["next"])
        self.assertIsNone(res.data["previous"])

    def test_second_page_returns_older_remainder_without_overlap(self):
        create_messages(self.conversation, self.user, 45)
        self.client.force_authenticate(user=self.user)

        first = self.client.get(self.url)
        second = self.client.get(self.url, {"page": 2})

        self.assertEqual(second.status_code, status.HTTP_200_OK)
        self.assertEqual(second.data["count"], 45)
        self.assertEqual(len(second.data["results"]), 15)
        self.assertIsNone(second.data["next"])
        self.assertIsNotNone(second.data["previous"])

        first_ids = {m["id"] for m in first.data["results"]}
        second_ids = {m["id"] for m in second.data["results"]}
        self.assertFalse(first_ids & second_ids)
        self.assertEqual(len(first_ids | second_ids), 45)

        oldest_on_first = min(m["created_at"] for m in first.data["results"])
        newest_on_second = max(
            m["created_at"] for m in second.data["results"]
        )
        self.assertLess(newest_on_second, oldest_on_first)

    def test_messages_are_ordered_newest_first_across_pages(self):
        create_messages(self.conversation, self.user, 45)
        self.client.force_authenticate(user=self.user)

        first = self.client.get(self.url)
        second = self.client.get(self.url, {"page": 2})

        bodies = [
            m["body"]
            for m in first.data["results"] + second.data["results"]
        ]
        expected = [f"msg {i}" for i in range(44, -1, -1)]
        self.assertEqual(bodies, expected)

    def test_page_past_end_returns_404(self):
        create_messages(self.conversation, self.user, 12)
        self.client.force_authenticate(user=self.user)

        res = self.client.get(self.url, {"page": 2})

        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_only_messages_of_requested_conversation_are_returned(self):
        other_conversation = Conversation.objects.create(
            type=Conversation.TYPE_PRIVATE
        )
        ConversationMembership.objects.create(
            user=self.user, conversation=other_conversation
        )
        create_messages(other_conversation, self.user, 7)
        create_messages(self.conversation, self.user, 3)
        self.client.force_authenticate(user=self.user)

        res = self.client.get(self.url)

        self.assertEqual(res.data["count"], 3)

    def test_conversation_list_still_returns_200(self):
        create_messages(self.conversation, self.user, 3)
        self.client.force_authenticate(user=self.user)

        res = self.client.get(reverse("conversation-list"))

        self.assertEqual(res.status_code, status.HTTP_200_OK)
