from django.db.models.signals import post_save
from django.dispatch import receiver

from listings.models import Listing

from .models import Conversation


@receiver(post_save, sender=Listing)
def create_public_conversation(sender, instance, created, **kwargs):
    if created:
        Conversation.objects.get_or_create(
            type=Conversation.TYPE_PUBLIC,
            listing=instance,
        )


@receiver(post_save, sender=Listing)
def close_conversation_on_listing_end(sender, instance, **kwargs):
    if instance.status in (
        Listing.STATUS_FOUND,
        Listing.STATUS_RETURNED,
        Listing.STATUS_EXPIRED,
    ):
        Conversation.objects.filter(listing=instance).update(is_closed=True)
