from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.test import TestCase

from chats.models import Conversation, ConversationMembership, Message, MessageReadStatus

User = get_user_model()


def create_user(username="user1", email="user1@example.com"):
    return User.objects.create_user(username=username, email=email, password="pass123")


class ConversationModelTests(TestCase):
    def test_is_closed_defaults_to_false(self):
        conversation = Conversation.objects.create(type=Conversation.TYPE_PRIVATE)
        self.assertFalse(conversation.is_closed)

    def test_created_at_is_set_automatically(self):
        conversation = Conversation.objects.create(type=Conversation.TYPE_PRIVATE)
        self.assertIsNotNone(conversation.created_at)


class ConversationMembershipModelTests(TestCase):
    def setUp(self):
        self.user = create_user()
        self.conversation = Conversation.objects.create(type=Conversation.TYPE_PRIVATE)

    def test_is_archived_defaults_to_false(self):
        membership = ConversationMembership.objects.create(
            user=self.user, conversation=self.conversation
        )
        self.assertFalse(membership.is_archived)

    def test_duplicate_membership_raises_integrity_error(self):
        ConversationMembership.objects.create(user=self.user, conversation=self.conversation)
        with self.assertRaises(IntegrityError):
            ConversationMembership.objects.create(user=self.user, conversation=self.conversation)


class MessageModelTests(TestCase):
    def setUp(self):
        self.user = create_user()
        self.conversation = Conversation.objects.create(type=Conversation.TYPE_PRIVATE)

    def test_messages_ordered_by_created_at(self):
        msg1 = Message.objects.create(conversation=self.conversation, sender=self.user, body="first")
        msg2 = Message.objects.create(conversation=self.conversation, sender=self.user, body="second")
        messages = list(self.conversation.messages.all())
        self.assertEqual(messages[0], msg1)
        self.assertEqual(messages[1], msg2)


class MessageReadStatusModelTests(TestCase):
    def setUp(self):
        self.user = create_user()
        self.conversation = Conversation.objects.create(type=Conversation.TYPE_PRIVATE)
        self.message = Message.objects.create(
            conversation=self.conversation, sender=self.user, body="hello"
        )

    def test_duplicate_read_status_raises_integrity_error(self):
        MessageReadStatus.objects.create(message=self.message, user=self.user)
        with self.assertRaises(IntegrityError):
            MessageReadStatus.objects.create(message=self.message, user=self.user)
