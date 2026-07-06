"""
Tests for listings periodic tasks
"""

from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from notifications.models import Notification

from ..models import Listing
from ..tasks import notify_expiring_listings

User = get_user_model()


def create_user(username="owner", email="owner@example.com"):
    return User.objects.create_user(
        username=username, email=email, password="testpass123"
    )


def create_listing(user, **params):
    defaults = {
        "type": Listing.TYPE_LOST,
        "title": "Lost Dog",
        "description": "Lost near park",
    }
    defaults.update(params)
    return Listing.objects.create(user=user, **defaults)


def set_expiry(listing, expires_at, expiring_notified_at=None):
    """Set expiry fields directly, bypassing model save() logic."""
    Listing.objects.filter(pk=listing.pk).update(
        expires_at=expires_at, expiring_notified_at=expiring_notified_at
    )
    listing.refresh_from_db()


class NotifyExpiringListingsTaskTests(TestCase):
    def setUp(self):
        self.user = create_user()

    @patch("listings.tasks.dispatch_notification")
    def test_notifies_only_listings_expiring_within_24h(self, mock_dispatch):
        expiring = create_listing(self.user, title="Expiring")
        set_expiry(expiring, timezone.now() + timedelta(hours=12))

        later = create_listing(self.user, title="Later")
        set_expiry(later, timezone.now() + timedelta(days=3))

        already = create_listing(self.user, title="Already warned")
        set_expiry(
            already,
            timezone.now() + timedelta(hours=6),
            expiring_notified_at=timezone.now(),
        )

        notify_expiring_listings()

        mock_dispatch.assert_called_once()
        kwargs = mock_dispatch.call_args.kwargs
        self.assertEqual(kwargs["user_id"], self.user.id)
        self.assertEqual(
            kwargs["event_type"], Notification.EVENT_LISTING_EXPIRING
        )
        self.assertEqual(kwargs["data"], {"listing_id": expiring.id})

        expiring.refresh_from_db()
        self.assertIsNotNone(expiring.expiring_notified_at)

    @patch("listings.tasks.dispatch_notification")
    def test_warning_is_sent_only_once(self, mock_dispatch):
        expiring = create_listing(self.user, title="Expiring")
        set_expiry(expiring, timezone.now() + timedelta(hours=12))

        notify_expiring_listings()
        notify_expiring_listings()

        mock_dispatch.assert_called_once()

    @patch("listings.tasks.dispatch_notification")
    def test_skips_expired_listing(self, mock_dispatch):
        expired = create_listing(self.user, title="Expired")
        set_expiry(expired, timezone.now() - timedelta(hours=1))

        notify_expiring_listings()

        mock_dispatch.assert_not_called()
