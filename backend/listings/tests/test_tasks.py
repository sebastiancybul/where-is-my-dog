"""
Tests for listings periodic tasks
"""

from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from chats.models import Conversation
from notifications.models import Notification

from ..models import Listing
from ..tasks import check_and_expire_listings, notify_expiring_listings

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


class CheckAndExpireListingsTaskTests(TestCase):
    def setUp(self):
        self.user = create_user()

    def test_expires_past_listings_and_closes_conversations(self):
        expired = create_listing(self.user, title="Expired")
        set_expiry(expired, timezone.now() - timedelta(hours=1))
        active = create_listing(self.user, title="Active")
        set_expiry(active, timezone.now() + timedelta(days=3))
        found = create_listing(self.user, title="Found")
        found.status = Listing.STATUS_FOUND
        found.save()
        set_expiry(found, timezone.now() - timedelta(hours=1))
        Conversation.objects.filter(listing=found).update(is_closed=False)

        result = check_and_expire_listings()

        self.assertEqual(result, "Expired 1 listings")

        expired.refresh_from_db()
        self.assertEqual(expired.status, Listing.STATUS_EXPIRED)
        self.assertTrue(
            Conversation.objects.get(
                listing=expired, type=Conversation.TYPE_PUBLIC
            ).is_closed
        )

        active.refresh_from_db()
        self.assertEqual(active.status, Listing.STATUS_ACTIVE)
        self.assertFalse(
            Conversation.objects.get(
                listing=active, type=Conversation.TYPE_PUBLIC
            ).is_closed
        )

        found.refresh_from_db()
        self.assertEqual(found.status, Listing.STATUS_FOUND)
        self.assertFalse(
            Conversation.objects.get(
                listing=found, type=Conversation.TYPE_PUBLIC
            ).is_closed
        )

    def test_no_expired_listings(self):
        listing = create_listing(self.user)

        result = check_and_expire_listings()

        self.assertEqual(result, "Expired 0 listings")
        listing.refresh_from_db()
        self.assertEqual(listing.status, Listing.STATUS_ACTIVE)
