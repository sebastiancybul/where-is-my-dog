"""
Tests for the listings API
"""

from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.gis.geos import Point

from listings.models import Listing, Location
from notifications.models import Notification

LISTINGS_URL = reverse("listing-list")


def nearby_url():
    """Generate URL for nearby listings endpoint"""
    return reverse("listing-nearby")


def check_similar_url():
    """Generate URL for check-similar endpoint"""
    return reverse("listing-check-similar")


def detail_url(listing_id):
    """Generate URL for listing detail"""
    return reverse("listing-detail", args=[listing_id])


def mark_found_url(listing_id):
    """Generate URL for mark_found action"""
    return reverse("listing-mark-found", args=[listing_id])


def upload_photo_url(listing_id):
    """Generate URL for upload_photo action"""
    return reverse("listing-upload-photo", args=[listing_id])


def delete_photo_url(listing_id, photo_id):
    """Generate URL for delete_photo action"""
    return reverse("listing-delete-photo", args=[listing_id, photo_id])


def add_location_url(listing_id):
    """Generate URL for add_location action"""
    return reverse("listing-add-location", args=[listing_id])


def delete_location_url(listing_id, location_id):
    """Generate URL for delete_location action"""
    return reverse("listing-delete-location", args=[listing_id, location_id])


USERNAME = "janek123"
EMAIL = "test@example.com"
PASSWORD = "testpass123"


def create_user(**params):
    """Create and return a new user"""
    defaults = {"username": USERNAME, "email": EMAIL, "password": PASSWORD}

    defaults.update(params)
    return get_user_model().objects.create_user(**defaults)


def create_listing(user, point=None, **params):
    """
    Helper function to create a listing with location.
    Returns created listing object.
    """
    defaults = {
        "type": Listing.TYPE_FOUND,
        "title": "Found Golden Retriever",
        "description": "Found near park, very friendly dog",
        "breed": "Golden Retriever",
        "size": Listing.SIZE_LARGE,
        "color": "Golden",
        "gender": Listing.GENDER_UNKNOWN,
        "has_collar": True,
        "collar_color": "Red",
        "search_radius_km": 5,
    }
    defaults.update(params)

    listing = Listing.objects.create(user=user, **defaults)

    # Create default location (Lublin)
    if point is None:
        point = Point(22.5684, 51.2465, srid=4326)
    Location.objects.create(
        listing=listing, point=point, added_by_user=user, is_primary=True
    )

    return listing


class PublicListingsApiTests(APITestCase):
    """Tests for unauthenticated users"""

    def setUp(self):
        """Create test data before each test"""
        self.user = create_user()
        self.listing = create_listing(self.user)

    def test_list_listings_success(self):
        """Test that unauthenticated users can view listings list"""
        create_listing(self.user, title="Found Beagle")

        res = self.client.get(LISTINGS_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data["results"]), 2)

    def test_filter_listings_multi_select(self):
        """Test filtering listings with multiple values (comma-separated)."""
        create_listing(
            self.user, title="Small male", size="small", gender="male"
        )
        create_listing(
            self.user, title="Medium female", size="medium", gender="female"
        )
        create_listing(
            self.user, title="Large male", size="large", gender="male"
        )

        # Multi-select size: small,medium → should return 2
        res = self.client.get(LISTINGS_URL, {"size": "small,medium"})

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        titles = [r["title"] for r in res.data["results"]]
        self.assertIn("Small male", titles)
        self.assertIn("Medium female", titles)
        self.assertNotIn("Large male", titles)

    def test_retrieve_listing_detail_success(self):
        """Test that unauthenticated users can view listing details"""
        url = detail_url(self.listing.id)
        res = self.client.get(url)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["id"], self.listing.id)
        self.assertEqual(res.data["title"], self.listing.title)
        self.assertIn("primary_location", res.data)

    def test_nearby_listings_success(self):
        """Test finding nearby listings without authentication"""
        # Create additional listing in different location
        create_listing(
            self.user,
            point=Point(
                22.5487, 51.2371
            ),  # Nadbystrzycka 1,7km km from the 22.5684, 51.2465 # noqa
            title="Another dog",
        )

        # Search near Lublin center
        url = nearby_url()
        res = self.client.get(
            url, {"latitude": 51.2465, "longitude": 22.5684, "radius_km": 1}
        )

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(
            len(res.data), 1
        )  # self.listing 22.5684, 51.2465 <1km # noqa

    def test_create_listing_fails_unauthenticated(self):
        """Test that creating listing requires authentication"""
        payload = {
            "type": "found",
            "title": "Found Dog",
            "description": "Test",
        }
        res = self.client.post(LISTINGS_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_mark_found_fails_unauthenticated(self):
        """Test marking listing as found requires authentication"""
        url = mark_found_url(self.listing.id)
        res = self.client.post(url)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateListingsApiTests(APITestCase):
    """Tests for authenticated users"""

    def setUp(self):
        """Create test users and authenticate"""
        self.user = create_user(username="user1", email="user1@example.com")
        self.other_user = create_user(
            username="user2", email="user2@example.com"
        )
        self.client.force_authenticate(user=self.user)

        # Create listings for different users
        self.own_listing = create_listing(self.user, title="My Dog")
        self.other_listing = create_listing(
            self.other_user, title="Other User Dog"
        )

    def test_create_listing_success(self):
        """Test creating a new listing as authenticated user"""
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
        res = self.client.post(LISTINGS_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data["title"], payload["title"])

        # Verify listing was created with correct user
        listing = Listing.objects.get(id=res.data["id"])
        self.assertEqual(listing.user, self.user)

    def test_update_own_listing_success(self):
        """Test updating own listing"""
        url = detail_url(self.own_listing.id)
        payload = {"title": "Updated Title"}
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.own_listing.refresh_from_db()
        self.assertEqual(self.own_listing.title, payload["title"])

    def test_update_other_user_listing_fails(self):
        """Test updating another user's listing fails"""
        url = detail_url(self.other_listing.id)
        payload = {"title": "Hacked Title"}
        res = self.client.patch(url, payload)

        self.assertIn(
            res.status_code,
            [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND],
        )

    def test_delete_own_listing_success(self):
        """Test deleting own listing"""
        url = detail_url(self.own_listing.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(
            Listing.objects.filter(id=self.own_listing.id).exists()
        )

    def test_delete_other_user_listing_fails(self):
        """Test deleting another user's listing fails"""
        url = detail_url(self.other_listing.id)
        res = self.client.delete(url)

        self.assertIn(
            res.status_code,
            [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND],
        )

        self.assertTrue(
            Listing.objects.filter(id=self.other_listing.id).exists()
        )

    def test_mark_found_own_listing_success(self):
        """Test marking own listing as found/returned"""
        found_listing = create_listing(
            self.user, type=Listing.TYPE_FOUND, title="Found Dog"
        )

        url = mark_found_url(found_listing.id)
        res = self.client.post(url)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        found_listing.refresh_from_db()
        self.assertEqual(found_listing.status, Listing.STATUS_RETURNED)

    def test_mark_found_other_user_listing_fails(self):
        """Test marking another user's listing fails"""
        url = mark_found_url(self.other_listing.id)
        res = self.client.post(url)

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("detail", res.data)


class LocationTests(APITestCase):
    """Tests for location functionality"""

    def setUp(self):
        """Create test user and listing"""
        self.user = create_user()
        self.client.force_authenticate(user=self.user)
        self.listing = create_listing(self.user)

    def test_add_location_to_listing_success(self):
        """Test adding new location to listing"""
        url = add_location_url(self.listing.id)

        payload = {
            "point": {
                "type": "Point",
                "coordinates": [22.5700, 51.2500],  # [lng, lat]
            },
            "address": "New location in Lublin",
            "location_type": "exact",
            "notes": "Dog spotted here",
        }

        res = self.client.post(url, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(self.listing.locations.count(), 2)

    @patch("listings.views.listing.dispatch_notification")
    def test_add_location_by_other_user_notifies_owner(self, mock_dispatch):
        reporter = create_user(
            username="reporter", email="reporter@example.com"
        )
        self.client.force_authenticate(user=reporter)
        url = add_location_url(self.listing.id)
        payload = {
            "point": {"type": "Point", "coordinates": [22.5700, 51.2500]}
        }

        res = self.client.post(url, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        mock_dispatch.assert_called_once()
        kwargs = mock_dispatch.call_args.kwargs
        self.assertEqual(kwargs["user_id"], self.user.id)
        self.assertEqual(
            kwargs["event_type"], Notification.EVENT_LOCATION_REPORTED
        )
        self.assertEqual(kwargs["data"]["listing_id"], self.listing.id)

    @patch("listings.views.listing.dispatch_notification")
    def test_add_location_by_owner_does_not_notify(self, mock_dispatch):
        url = add_location_url(self.listing.id)
        payload = {
            "point": {"type": "Point", "coordinates": [22.5700, 51.2500]}
        }

        res = self.client.post(url, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        mock_dispatch.assert_not_called()

    def test_new_location_becomes_primary(self):
        """Test that newly added location becomes primary"""
        url = add_location_url(self.listing.id)

        payload = {
            "point": {"type": "Point", "coordinates": [22.5700, 51.2500]}
        }

        res = self.client.post(url, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        # New location should be primary
        new_location = Location.objects.get(id=res.data["id"])
        self.assertTrue(new_location.is_primary)

        # Old location should no longer be primary
        old_location = self.listing.locations.exclude(
            id=new_location.id
        ).first()
        self.assertFalse(old_location.is_primary)

    def test_delete_location_as_listing_owner_success(self):
        """Test that listing owner can delete a location"""
        location = self.listing.locations.first()
        url = delete_location_url(self.listing.id, location.id)

        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertFalse(Location.objects.filter(id=location.id).exists())

    def test_delete_location_as_location_adder_success(self):
        """Test that user who added the location can delete it"""
        other_user = create_user(username="other", email="other@example.com")
        location = Location.objects.create(
            listing=self.listing,
            point=Point(22.5700, 51.2500),
            added_by_user=other_user,
            is_primary=False,
        )

        self.client.force_authenticate(user=other_user)
        url = delete_location_url(self.listing.id, location.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertFalse(Location.objects.filter(id=location.id).exists())

    def test_delete_location_unauthorized_user_fails(self):
        """Test that random user cannot delete a location"""
        other_user = create_user(username="other", email="other@example.com")
        self.client.force_authenticate(user=other_user)

        location = self.listing.locations.first()
        url = delete_location_url(self.listing.id, location.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(Location.objects.filter(id=location.id).exists())


class DuplicateDetectionTests(APITestCase):
    """Tests for duplicate/similar listing detection"""

    def setUp(self):
        """Create test user and listings"""
        self.user = create_user()
        self.client.force_authenticate(user=self.user)

        self.existing_found = create_listing(
            self.user,
            type=Listing.TYPE_FOUND,
            breed="Labrador",
            size=Listing.SIZE_LARGE,
            has_collar=True,
            collar_color="Red",
        )

    def test_check_similar_finds_exact_match(self):
        """Test finding similar listings with exact characteristics"""
        url = check_similar_url()

        payload = {
            "search_type": "found",
            "point": {"type": "Point", "coordinates": [22.5684, 51.2465]},
            "breed": "Labrador",
            "size": "large",
            "has_collar": True,
            "collar_color": "Red",
        }

        res = self.client.post(url, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]["id"], self.existing_found.id)

    def test_check_similar_no_match_different_breed(self):
        """Test no match when breed is different"""
        url = check_similar_url()

        payload = {
            "search_type": "found",
            "point": {"type": "Point", "coordinates": [22.5684, 51.2465]},
            "breed": "Beagle",
            "size": "large",
            "has_collar": True,
            "collar_color": "Red",
        }

        res = self.client.post(url, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 0)
