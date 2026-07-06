from datetime import timedelta

from celery import shared_task

from django.utils import timezone

from notifications.dispatch import dispatch_notification
from notifications.models import Notification

from .models import Listing


@shared_task
def check_and_expire_listings():
    """
    Periodic task runs every two hours to check and expire listings.
    Marks listings as expired if expires_at has passed.
    """
    now = timezone.now()

    expired_listings = Listing.objects.filter(
        expires_at__lt=now, status=Listing.STATUS_ACTIVE
    )

    count = expired_listings.update(status=Listing.STATUS_EXPIRED)

    return f"Expired {count} listings"


@shared_task
def notify_expiring_listings():
    """
    Periodic task that warns owners about active listings expiring within
    the next 24 hours. Sent once per listing, guarded by
    expiring_notified_at.
    """
    now = timezone.now()
    threshold = now + timedelta(hours=24)

    expiring = Listing.objects.filter(
        status=Listing.STATUS_ACTIVE,
        expires_at__gt=now,
        expires_at__lte=threshold,
        expiring_notified_at__isnull=True,
    )

    count = 0
    for listing in expiring:
        dispatch_notification(
            user_id=listing.user_id,
            event_type=Notification.EVENT_LISTING_EXPIRING,
            title=listing.title,
            body="Your listing expires soon. Bump it to keep it active.",
            data={"listing_id": listing.pk},
        )
        listing.expiring_notified_at = now
        listing.save(update_fields=["expiring_notified_at"])
        count += 1

    return f"Notified {count} expiring listings"
