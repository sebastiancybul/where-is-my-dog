from django.contrib.auth import get_user_model
from django.contrib.gis.db.models.fields import get_srid_info
from django.contrib.gis.geos import Point
from django.db import connection
from django.test.utils import CaptureQueriesContext
from rest_framework import status
from rest_framework.test import APITestCase

from chats.models import Conversation
from listings.models import Listing, Location, Photo
from listings.tests.test_listings_api import (
    LISTINGS_URL,
    check_similar_url,
    create_listing,
    detail_url,
    nearby_url,
)

User = get_user_model()

MAX_QUERIES = 10

LUBLIN_LNG = 22.5684
LUBLIN_LAT = 51.2465


def setUpModule():
    get_srid_info(4326, connection)


def create_user(name):
    return User.objects.create_user(
        username=name, email=f"{name}@example.com", password="testpass123"
    )


def create_photo(listing, order_index, thumbnail):
    return Photo.objects.create(
        listing=listing,
        cloudinary_url="listings/photos/sample",
        thumbnail_url=thumbnail,
        order_index=order_index,
    )


def add_location(listing, user, address, is_primary=False, offset=0.0):
    return Location.objects.create(
        listing=listing,
        added_by_user=user,
        point=Point(LUBLIN_LNG + offset, LUBLIN_LAT + offset, srid=4326),
        address=address,
        is_primary=is_primary,
    )


def public_conversation(listing):
    return Conversation.objects.get(
        listing=listing, type=Conversation.TYPE_PUBLIC
    )


def create_full_listing(owner, prefix, extra_locations=2, **params):
    """
    Listing with two photos, a primary location from create_listing and
    extra non-primary locations, each added by a different user.
    """
    listing = create_listing(owner, **params)
    listing.locations.update(address=f"{prefix} primary")
    create_photo(listing, 0, f"{prefix}-thumb-0")
    create_photo(listing, 1, f"{prefix}-thumb-1")
    for i in range(extra_locations):
        adder = create_user(f"{prefix}a{i}")
        add_location(listing, adder, f"{prefix} extra {i}", offset=0.001)
    return listing


class ListQueryCountTests(APITestCase):
    def setUp(self):
        self.owner = create_user("lqowner")

    def _count_queries(self, url, params=None):
        with CaptureQueriesContext(connection) as ctx:
            res = self.client.get(url, params)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        return len(ctx.captured_queries), len(res.data["results"])

    def test_list_query_count_does_not_grow_with_listings(self):
        create_full_listing(self.owner, "l0")
        count_small, size_small = self._count_queries(LISTINGS_URL)

        for i in range(1, 5):
            create_full_listing(self.owner, f"l{i}")
        count_large, size_large = self._count_queries(LISTINGS_URL)

        self.assertEqual((size_small, size_large), (1, 5))
        self.assertEqual(count_small, count_large)
        self.assertLessEqual(count_large, MAX_QUERIES)

    def test_nearby_query_count_does_not_grow_with_listings(self):
        params = {
            "latitude": LUBLIN_LAT,
            "longitude": LUBLIN_LNG,
            "radius_km": 5,
        }
        create_full_listing(self.owner, "n0")
        count_small, size_small = self._count_queries(nearby_url(), params)

        for i in range(1, 5):
            create_full_listing(self.owner, f"n{i}")
        count_large, size_large = self._count_queries(nearby_url(), params)

        self.assertEqual((size_small, size_large), (1, 5))
        self.assertEqual(count_small, count_large)
        self.assertLessEqual(count_large, MAX_QUERIES)


class DetailQueryCountTests(APITestCase):
    def setUp(self):
        self.owner = create_user("dqowner")

    def _count_queries(self, listing):
        with CaptureQueriesContext(connection) as ctx:
            res = self.client.get(detail_url(listing.id))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        return len(ctx.captured_queries), len(res.data["locations"])

    def test_detail_query_count_does_not_grow_with_locations(self):
        small = create_full_listing(self.owner, "ds", extra_locations=0)
        large = create_full_listing(self.owner, "dl", extra_locations=9)

        count_small, size_small = self._count_queries(small)
        count_large, size_large = self._count_queries(large)

        self.assertEqual((size_small, size_large), (1, 10))
        self.assertEqual(count_small, count_large)
        self.assertLessEqual(count_large, MAX_QUERIES)


class CheckSimilarQueryCountTests(APITestCase):
    def setUp(self):
        self.owner = create_user("cqowner")
        self.client.force_authenticate(user=self.owner)

    def _count_queries(self, breed):
        payload = {
            "search_type": "found",
            "point": {
                "type": "Point",
                "coordinates": [LUBLIN_LNG, LUBLIN_LAT],
            },
            "breed": breed,
            "size": "large",
            "has_collar": True,
            "collar_color": "Red",
        }
        with CaptureQueriesContext(connection) as ctx:
            res = self.client.post(check_similar_url(), payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        return len(ctx.captured_queries), res.data

    def _create_matches(self, prefix, breed, count):
        return [
            create_full_listing(
                self.owner,
                f"{prefix}{i}",
                type=Listing.TYPE_FOUND,
                breed=breed,
                size=Listing.SIZE_LARGE,
                has_collar=True,
                collar_color="Red",
            )
            for i in range(count)
        ]

    def test_check_similar_query_count_does_not_grow_with_matches(self):
        self._create_matches("cs", "Husky", 1)
        self._create_matches("cl", "Labrador", 4)

        count_small, data_small = self._count_queries("Husky")
        count_large, data_large = self._count_queries("Labrador")

        self.assertEqual((len(data_small), len(data_large)), (1, 4))
        self.assertEqual(count_small, count_large)
        self.assertLessEqual(count_large, MAX_QUERIES)

    def test_check_similar_returns_detail_fields(self):
        listing = self._create_matches("cc", "Husky", 1)[0]
        primary = listing.locations.get(is_primary=True)

        _, data = self._count_queries("Husky")

        self.assertEqual(data[0]["id"], listing.id)
        self.assertEqual(data[0]["primary_location"]["id"], primary.id)
        self.assertEqual(data[0]["photo_count"], 2)
        self.assertEqual(len(data[0]["locations"]), 3)
        self.assertEqual(
            data[0]["public_conversation_id"],
            public_conversation(listing).id,
        )
        self.assertFalse(data[0]["public_conversation_is_closed"])


class ListContentTests(APITestCase):
    def setUp(self):
        self.owner = create_user("lcowner")

    def _get_result(self, listing):
        res = self.client.get(LISTINGS_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        return next(r for r in res.data["results"] if r["id"] == listing.id)

    def test_primary_location_ignores_newer_non_primary(self):
        listing = create_full_listing(self.owner, "lp", extra_locations=2)

        data = self._get_result(listing)

        self.assertEqual(data["primary_location"], "lp primary")

    def test_primary_photo_uses_lowest_order_index(self):
        listing = create_listing(self.owner)
        create_photo(listing, 1, "thumb-second")
        create_photo(listing, 0, "thumb-primary")

        data = self._get_result(listing)

        self.assertEqual(data["primary_photo"], "thumb-primary")

    def test_listing_without_photos_has_no_primary_photo(self):
        listing = create_listing(self.owner)

        data = self._get_result(listing)

        self.assertIsNone(data["primary_photo"])

    def test_listing_without_primary_location_has_none(self):
        listing = create_listing(self.owner)
        listing.locations.update(is_primary=False)

        data = self._get_result(listing)

        self.assertIsNone(data["primary_location"])

    def test_nearby_uses_primary_location_and_photo(self):
        listing = create_full_listing(self.owner, "np", extra_locations=1)

        res = self.client.get(
            nearby_url(),
            {"latitude": LUBLIN_LAT, "longitude": LUBLIN_LNG},
        )

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        data = res.data["results"][0]
        self.assertEqual(data["id"], listing.id)
        self.assertEqual(data["primary_location"], "np primary")
        self.assertEqual(data["primary_photo"], "np-thumb-0")


class DetailContentTests(APITestCase):
    def setUp(self):
        self.owner = create_user("dcowner")

    def _get(self, listing):
        res = self.client.get(detail_url(listing.id))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        return res.data

    def test_primary_location_photo_count_and_adders(self):
        listing = create_full_listing(self.owner, "dp", extra_locations=2)
        primary = listing.locations.get(is_primary=True)

        data = self._get(listing)

        self.assertEqual(data["primary_location"]["id"], primary.id)
        self.assertEqual(data["primary_location"]["address"], "dp primary")
        self.assertEqual(data["photo_count"], 2)
        self.assertEqual(data["user"]["username"], "dcowner")
        adders = {
            loc["address"]: loc["added_by_user"]["username"]
            for loc in data["locations"]
        }
        self.assertEqual(
            adders,
            {
                "dp primary": "dcowner",
                "dp extra 0": "dpa0",
                "dp extra 1": "dpa1",
            },
        )

    def test_locations_keep_newest_first_order(self):
        listing = create_full_listing(self.owner, "do", extra_locations=2)

        data = self._get(listing)

        self.assertEqual(
            [loc["address"] for loc in data["locations"]],
            ["do extra 1", "do extra 0", "do primary"],
        )

    def test_listing_without_photos_or_primary_location(self):
        listing = create_listing(self.owner)
        listing.locations.update(is_primary=False)

        data = self._get(listing)

        self.assertIsNone(data["primary_location"])
        self.assertEqual(data["photo_count"], 0)

    def test_public_conversation_ignores_private_conversations(self):
        listing = create_listing(self.owner)
        # Recreate the public one after a private one, so an unfiltered
        # lookup ordered by pk would return the private conversation.
        public_conversation(listing).delete()
        Conversation.objects.create(
            type=Conversation.TYPE_PRIVATE, listing=listing, is_closed=True
        )
        public = Conversation.objects.create(
            type=Conversation.TYPE_PUBLIC, listing=listing
        )

        data = self._get(listing)

        self.assertEqual(data["public_conversation_id"], public.id)
        self.assertFalse(data["public_conversation_is_closed"])

    def test_public_conversation_closed(self):
        listing = create_listing(self.owner)
        conversation = public_conversation(listing)
        Conversation.objects.filter(pk=conversation.pk).update(
            is_closed=True
        )

        data = self._get(listing)

        self.assertEqual(data["public_conversation_id"], conversation.id)
        self.assertTrue(data["public_conversation_is_closed"])


class UnprefetchedResponseTests(APITestCase):
    """create and update serialize without the view's prefetches."""

    def setUp(self):
        self.owner = create_user("upowner")
        self.client.force_authenticate(user=self.owner)

    def test_create_response_fields(self):
        payload = {
            "type": "lost",
            "title": "Lost Beagle",
            "description": "Lost near park",
            "breed": "Beagle",
            "size": "medium",
            "color": "Brown",
            "has_collar": False,
            "search_radius_km": 5,
        }

        res = self.client.post(LISTINGS_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        listing = Listing.objects.get(id=res.data["id"])
        self.assertIsNone(res.data["primary_location"])
        self.assertEqual(res.data["photo_count"], 0)
        self.assertEqual(
            res.data["public_conversation_id"],
            public_conversation(listing).id,
        )
        self.assertFalse(res.data["public_conversation_is_closed"])

    def test_update_response_fields(self):
        listing = create_full_listing(self.owner, "up", extra_locations=2)
        conversation = public_conversation(listing)
        Conversation.objects.filter(pk=conversation.pk).update(
            is_closed=True
        )
        primary = listing.locations.get(is_primary=True)

        res = self.client.patch(detail_url(listing.id), {"title": "New"})

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["title"], "New")
        self.assertEqual(res.data["primary_location"]["id"], primary.id)
        self.assertEqual(res.data["photo_count"], 2)
        self.assertEqual(len(res.data["locations"]), 3)
        self.assertEqual(res.data["public_conversation_id"], conversation.id)
        self.assertTrue(res.data["public_conversation_is_closed"])
