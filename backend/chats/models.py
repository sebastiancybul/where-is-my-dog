from django.db import models

from django.conf import settings
from cloudinary.models import CloudinaryField


class Conversation(models.Model):
    TYPE_PUBLIC = 'public'
    TYPE_PRIVATE = 'private'
    TYPE_CHOICES = [
        (TYPE_PUBLIC, 'Public Chat'),
        (TYPE_PRIVATE, 'Private 1:1'),
    ]

    type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    listing = models.OneToOneField(
        'listings.Listing',
        on_delete=models.CASCADE,
        related_name='public_conversation',
        null=True,
        blank=True,
    )
    is_closed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)


class ConversationMembership(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='memberships',
    )
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name='memberships',
    )
    is_archived = models.BooleanField(default=False)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [('user', 'conversation')]


class Message(models.Model):
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name='messages',
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='sent_messages',
    )
    body = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']


class MessagePhoto(models.Model):
    message = models.ForeignKey(
        Message,
        on_delete=models.CASCADE,
        related_name='photos',
    )
    image = CloudinaryField('photo', folder='chats/photos')
    cloudinary_public_id = models.CharField(max_length=255, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['uploaded_at']


class MessageReadStatus(models.Model):
    message = models.ForeignKey(
        Message,
        on_delete=models.CASCADE,
        related_name='read_statuses',
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='message_read_statuses',
    )
    read_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [('message', 'user')]
