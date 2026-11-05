from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from chats.models import (
    Conversation,
    ConversationMembership,
    Message,
    MessagePhoto,
    MessageReadStatus,
)
from listings.models import Photo
from listings.tests.test_listings_api import create_listing

User = get_user_model()

# Generous ceiling: the real guard is that the count doesn't grow with data.
MAX_QUERIES = 10


def create_user(name):
    return User.objects.create_user(
        username=name, email=f"{name}@example.com", password="testpass123"
    )


def create_conversation(members, listing=None):
    conversation = Conversation.objects.create(
        type=Conversation.TYPE_PRIVATE, listing=listing
    )
    for member in members:
        ConversationMembership.objects.create(
            user=member, conversation=conversation
        )
    return conversation


def create_message(conversation, sender, created_at, readers=(), photo=True):
    message = Message.objects.create(
        conversation=conversation, sender=sender, body="hi"
    )
    Message.objects.filter(pk=message.pk).update(created_at=created_at)
    if photo:
        MessagePhoto.objects.create(
            message=message, image="chats/photos/sample"
        )
    for reader in readers:
        MessageReadStatus.objects.create(message=message, user=reader)
    return message


def create_listing_photo(listing, order_index, thumbnail):
    return Photo.objects.create(
        listing=listing,
        cloudinary_url="listings/photos/sample",
        thumbnail_url=thumbnail,
        order_index=order_index,
    )


class MessagesQueryCountTests(APITestCase):
    def setUp(self):
        self.user = create_user("qm1")
        self.other = create_user("qm2")
        self.client.force_authenticate(user=self.user)

    def _conversation_with_messages(self, count):
        conversation = create_conversation([self.user, self.other])
        base = timezone.now() - timedelta(days=1)
        for i in range(count):
            sender = self.user if i % 2 else self.other
            create_message(
                conversation,
                sender,
                base + timedelta(minutes=i),
                readers=[self.user, self.other],
                photo=i % 3 == 0,
            )
        return conversation

    def _count_queries(self, conversation):
        url = reverse("conversation-messages", args=[conversation.pk])
        with CaptureQueriesContext(connection) as ctx:
            res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        return len(ctx.captured_queries)

    def test_query_count_does_not_grow_with_messages(self):
        small = self._conversation_with_messages(1)
        large = self._conversation_with_messages(30)

        count_small = self._count_queries(small)
        count_large = self._count_queries(large)

        self.assertEqual(count_small, count_large)
        self.assertLessEqual(count_large, MAX_QUERIES)

    def test_read_by_lists_reader_ids(self):
        conversation = create_conversation([self.user, self.other])
        message = create_message(
            conversation,
            self.other,
            timezone.now(),
            readers=[self.user, self.other],
        )
        unread = create_message(
            conversation, self.user, timezone.now() + timedelta(minutes=1)
        )
        url = reverse("conversation-messages", args=[conversation.pk])

        res = self.client.get(url)

        by_id = {m["id"]: m for m in res.data["results"]}
        self.assertCountEqual(
            by_id[message.id]["read_by"], [self.user.id, self.other.id]
        )
        self.assertEqual(by_id[unread.id]["read_by"], [])
        self.assertEqual(by_id[message.id]["sender_username"], "qm2")
        self.assertEqual(len(by_id[message.id]["photos"]), 1)


class ConversationListQueryCountTests(APITestCase):
    def _user_with_conversations(self, name, count):
        user = create_user(name)
        base = timezone.now() - timedelta(days=1)
        for i in range(count):
            other = create_user(f"{name}o{i}")
            listing = create_listing(other, title=f"Dog {i}")
            create_listing_photo(listing, 0, f"thumb-{i}-0")
            create_listing_photo(listing, 1, f"thumb-{i}-1")
            conversation = create_conversation([user, other], listing)
            for j in range(3):
                create_message(
                    conversation,
                    other if j % 2 else user,
                    base + timedelta(minutes=i * 10 + j),
                    readers=[user, other],
                )
        return user

    def _count_queries(self, user):
        self.client.force_authenticate(user=user)
        with CaptureQueriesContext(connection) as ctx:
            res = self.client.get(reverse("conversation-list"))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        return len(ctx.captured_queries), len(res.data)

    def test_query_count_does_not_grow_with_conversations(self):
        small_user = self._user_with_conversations("ql1", 1)
        large_user = self._user_with_conversations("ql2", 10)

        count_small, size_small = self._count_queries(small_user)
        count_large, size_large = self._count_queries(large_user)

        self.assertEqual((size_small, size_large), (1, 10))
        self.assertEqual(count_small, count_large)
        self.assertLessEqual(count_large, MAX_QUERIES)


class ConversationListContentTests(APITestCase):
    def setUp(self):
        self.user = create_user("cl1")
        self.other = create_user("cl2")
        self.client.force_authenticate(user=self.user)
        self.url = reverse("conversation-list")

    def _get_conversation(self, conversation):
        res = self.client.get(self.url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        return next(c for c in res.data if c["id"] == conversation.id)

    def test_last_message_is_newest(self):
        conversation = create_conversation([self.user, self.other])
        base = timezone.now() - timedelta(hours=1)
        newest = create_message(
            conversation, self.other, base + timedelta(minutes=5)
        )
        # Created after the newest one so id order differs from time order.
        create_message(conversation, self.user, base)

        data = self._get_conversation(conversation)

        self.assertEqual(data["last_message"]["id"], newest.id)

    def test_last_message_tie_on_created_at_picks_highest_id(self):
        conversation = create_conversation([self.user, self.other])
        same_time = timezone.now() - timedelta(minutes=5)
        create_message(conversation, self.user, same_time)
        create_message(conversation, self.other, same_time)
        latest = create_message(conversation, self.user, same_time)

        data = self._get_conversation(conversation)

        self.assertEqual(data["last_message"]["id"], latest.id)

    def test_conversation_without_messages_has_no_last_message(self):
        conversation = create_conversation([self.user, self.other])

        data = self._get_conversation(conversation)

        self.assertIsNone(data["last_message"])

    def test_other_participant_is_never_requester(self):
        first = create_conversation([self.user, self.other])
        third = create_user("cl3")
        # Requester joins last so a naive "first membership" would be wrong
        # in one conversation and right in the other.
        second = create_conversation([third, self.user])

        first_data = self._get_conversation(first)
        second_data = self._get_conversation(second)

        self.assertEqual(first_data["other_participant"]["id"], self.other.id)
        self.assertEqual(second_data["other_participant"]["id"], third.id)
        self.assertEqual(
            second_data["other_participant"]["username"], "cl3"
        )

    def test_listing_photo_uses_lowest_order_index(self):
        listing = create_listing(self.other)
        create_listing_photo(listing, 1, "thumb-second")
        create_listing_photo(listing, 0, "thumb-primary")
        conversation = create_conversation([self.user, self.other], listing)

        data = self._get_conversation(conversation)

        self.assertEqual(data["listing_photo"], "thumb-primary")
        self.assertEqual(data["listing_title"], listing.title)

    def test_listing_without_photos_has_no_listing_photo(self):
        listing = create_listing(self.other)
        conversation = create_conversation([self.user, self.other], listing)

        data = self._get_conversation(conversation)

        self.assertIsNone(data["listing_photo"])

    def test_conversation_without_listing_has_no_listing_fields(self):
        conversation = create_conversation([self.user, self.other])

        data = self._get_conversation(conversation)

        self.assertIsNone(data["listing_title"])
        self.assertIsNone(data["listing_photo"])

    def test_public_conversation_from_signal_not_listed_for_non_member(
        self,
    ):
        create_listing(self.user)

        res = self.client.get(self.url)

        self.assertEqual(res.data, [])


class ConversationRetrieveTests(APITestCase):
    def setUp(self):
        self.user = create_user("cr1")
        self.other = create_user("cr2")
        self.client.force_authenticate(user=self.user)

    def test_retrieve_returns_last_message_and_other_participant(self):
        listing = create_listing(self.other)
        create_listing_photo(listing, 1, "thumb-second")
        create_listing_photo(listing, 0, "thumb-primary")
        conversation = create_conversation([self.user, self.other], listing)
        base = timezone.now() - timedelta(hours=1)
        create_message(conversation, self.user, base)
        newest = create_message(
            conversation,
            self.other,
            base + timedelta(minutes=5),
            readers=[self.user],
        )
        url = reverse("conversation-detail", args=[conversation.pk])

        res = self.client.get(url)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["last_message"]["id"], newest.id)
        self.assertEqual(res.data["last_message"]["read_by"], [self.user.id])
        self.assertEqual(res.data["other_participant"]["id"], self.other.id)
        self.assertEqual(res.data["listing_photo"], "thumb-primary")

    def test_retrieve_without_messages_has_no_last_message(self):
        conversation = create_conversation([self.user, self.other])
        url = reverse("conversation-detail", args=[conversation.pk])

        res = self.client.get(url)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIsNone(res.data["last_message"])
        self.assertIsNone(res.data["listing_title"])
