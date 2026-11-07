"""
Tests for creating a listing with its first location in one request
"""

from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APITestCase

from chats.models import Conversation
from listings.models import Listing, Location

LISTINGS_URL = reverse("listing-list")
LOCATION_ERROR = (
    "Locations can't be changed here. "
    "Use the listing's location endpoint instead."
)


def detail_url(listing_id):
    return reverse("listing-detail", args=[listing_id])


def create_user(**params):
    defaults = {
        "username": "owner",
        "email": "owner@example.com",
        "password": "testpass123",
    }
    defaults.update(params)
    return get_user_model().objects.create_user(**defaults)


def listing_payload(**params):
    payload = {
        "type": "lost",
        "title": "Lost Beagle",
        "description": "Lost my beagle near park",
        "breed": "Beagle",
        "size": "medium",
        "color": "Brown",
        "has_collar": True,
        "collar_color": "Blue",
        "search_radius_km": 5,
    }
    payload.update(params)
    return payload


def location_payload(**params):
    payload = {
        "point": {"type": "Point", "coordinates": [22.57, 51.25]},
        "address": "Lublin, Old Town",
        "location_type": "approximate",
        "is_primary": False,
        "notes": "",
        "accuracy_meters": 300,
    }
    payload.update(params)
    return payload


class CreateListingWithLocationTests(APITestCase):
    def setUp(self):
        self.user = create_user()
        self.client.force_authenticate(user=self.user)

    def test_create_with_location_saves_primary_location(self):
        payload = listing_payload(location=location_payload())

        res = self.client.post(LISTINGS_URL, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        listing = Listing.objects.get(id=res.data["id"])
        self.assertEqual(listing.user, self.user)

        location = Location.objects.get(listing=listing)
        self.assertTrue(location.is_primary)
        self.assertEqual(location.added_by_user, self.user)
        self.assertEqual(location.address, "Lublin, Old Town")
        self.assertEqual(location.location_type, "approximate")
        self.assertEqual(location.accuracy_meters, 300)
        self.assertAlmostEqual(location.point.x, 22.57)
        self.assertAlmostEqual(location.point.y, 51.25)

        self.assertTrue(
            Conversation.objects.filter(
                listing=listing, type=Conversation.TYPE_PUBLIC
            ).exists()
        )

        self.assertNotIn("location", res.data)
        self.assertEqual(res.data["primary_location"]["id"], location.id)
        self.assertEqual(len(res.data["locations"]), 1)
        self.assertIsNotNone(res.data["public_conversation_id"])

    def test_create_with_location_failure_rolls_back(self):
        self.client.raise_request_exception = False
        listings_before = Listing.objects.count()
        conversations_before = Conversation.objects.count()
        payload = listing_payload(location=location_payload())

        with patch(
            "listings.serializers.listing.Location.objects.create",
            side_effect=RuntimeError("db down"),
        ):
            res = self.client.post(LISTINGS_URL, payload, format="json")

        self.assertEqual(
            res.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR
        )
        self.assertEqual(Listing.objects.count(), listings_before)
        self.assertEqual(Location.objects.count(), 0)
        self.assertEqual(Conversation.objects.count(), conversations_before)

    def test_create_with_location_missing_point_fails(self):
        location = location_payload()
        del location["point"]
        payload = listing_payload(location=location)

        res = self.client.post(LISTINGS_URL, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("point", res.data["location"])
        self.assertFalse(Listing.objects.exists())
        self.assertFalse(Conversation.objects.exists())

    def test_create_with_invalid_geojson_fails(self):
        payload = listing_payload(
            location=location_payload(point={"type": "Point"})
        )

        res = self.client.post(LISTINGS_URL, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("location", res.data)
        self.assertFalse(Listing.objects.exists())
        self.assertFalse(Conversation.objects.exists())

    def test_create_without_location_success(self):
        res = self.client.post(
            LISTINGS_URL, listing_payload(), format="json"
        )

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        listing = Listing.objects.get(id=res.data["id"])
        self.assertFalse(listing.locations.exists())
        self.assertIsNone(res.data["primary_location"])
        self.assertEqual(res.data["locations"], [])

    def test_create_with_location_unauthenticated_fails(self):
        self.client.force_authenticate(user=None)
        payload = listing_payload(location=location_payload())

        res = self.client.post(LISTINGS_URL, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertFalse(Listing.objects.exists())
        self.assertFalse(Location.objects.exists())


class UpdateListingLocationTests(APITestCase):
    def setUp(self):
        self.user = create_user()
        self.client.force_authenticate(user=self.user)
        res = self.client.post(
            LISTINGS_URL,
            listing_payload(location=location_payload()),
            format="json",
        )
        self.listing = Listing.objects.get(id=res.data["id"])
        self.location = self.listing.locations.get()

    def test_patch_with_location_fails(self):
        payload = {
            "title": "New title",
            "location": location_payload(
                point={"type": "Point", "coordinates": [21.0, 52.2]}
            ),
        }

        res = self.client.patch(
            detail_url(self.listing.id), payload, format="json"
        )

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(str(res.data["location"][0]), LOCATION_ERROR)
        self.listing.refresh_from_db()
        self.assertEqual(self.listing.title, "Lost Beagle")
        self.assertEqual(self.listing.locations.count(), 1)

    def test_put_with_location_fails(self):
        payload = listing_payload(
            title="New title", location=location_payload()
        )

        res = self.client.put(
            detail_url(self.listing.id), payload, format="json"
        )

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(str(res.data["location"][0]), LOCATION_ERROR)
        self.listing.refresh_from_db()
        self.assertEqual(self.listing.title, "Lost Beagle")
        self.assertEqual(self.listing.locations.count(), 1)

    def test_patch_without_location_success(self):
        res = self.client.patch(
            detail_url(self.listing.id),
            {"title": "New title"},
            format="json",
        )

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.listing.refresh_from_db()
        self.assertEqual(self.listing.title, "New title")
        self.assertEqual(
            list(self.listing.locations.all()), [self.location]
        )
