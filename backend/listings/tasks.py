from celery import shared_task

from django.utils import timezone
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
