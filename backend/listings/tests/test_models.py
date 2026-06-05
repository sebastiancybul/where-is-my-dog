"""
Tests for Listing, Photo and Location models
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.contrib.gis.geos import Point
from django.utils import timezone
from django.core.exceptions import ValidationError
from datetime import timedelta

from ..models import Listing, Photo, Location

User = get_user_model()


def create_user(username="testuser", email="test@example.com"):
    """Helper function to create a test user"""
    return User.objects.create_user(
        username=username, email=email, password="testpass123"
    )


class ListingModelTests(TestCase):
    """Tests for Listing model"""

    def setUp(self):
        """Create a test user for listings"""
        self.user = create_user()

    def test_create_found_listing_successful(self):
        """Test creating a found dog listing"""
        listing = Listing.objects.create(
            user=self.user,
            type=Listing.TYPE_FOUND,
            title="Found Golden Retriever",
            description="Found near park",
            breed="Golden Retriever",
            size=Listing.SIZE_LARGE,
        )

        self.assertEqual(listing.user, self.user)
        self.assertEqual(listing.type, Listing.TYPE_FOUND)
        self.assertEqual(listing.status, Listing.STATUS_ACTIVE)
        self.assertEqual(listing.title, "Found Golden Retriever")
        self.assertTrue(listing.is_active)

    def test_create_lost_listing_successful(self):
        """Test creating a lost dog listing"""
        listing = Listing.objects.create(
            user=self.user,
            type=Listing.TYPE_LOST,
            title="Lost Beagle",
            description="Lost on Monday",
            breed="Beagle",
            size=Listing.SIZE_MEDIUM,
        )

        self.assertEqual(listing.type, Listing.TYPE_LOST)
        self.assertEqual(listing.status, Listing.STATUS_ACTIVE)

    def test_found_listing_expires_at_set_automatically(self):
        """Test found listing gets expires_at set to 48h from now"""
        before_creation = timezone.now()

        listing = Listing.objects.create(
            user=self.user,
            type=Listing.TYPE_FOUND,
            title="Found Dog",
            description="Test",
        )

        after_creation = timezone.now()
        expected_min = before_creation + timedelta(days=2)
        expected_max = after_creation + timedelta(days=2)

        self.assertIsNotNone(listing.expires_at)
        self.assertGreaterEqual(listing.expires_at, expected_min)
        self.assertLessEqual(listing.expires_at, expected_max)

    def test_lost_listing_expires_at_set_automatically(self):
        """Test lost listing gets expires_at set to 5 days from now"""
        before_creation = timezone.now()

        listing = Listing.objects.create(
            user=self.user,
            type=Listing.TYPE_LOST,
            title="Lost Dog",
            description="Test",
        )

        after_creation = timezone.now()
        expected_min = before_creation + timedelta(days=5)
        expected_max = after_creation + timedelta(days=5)

        self.assertIsNotNone(listing.expires_at)
        self.assertGreaterEqual(listing.expires_at, expected_min)
        self.assertLessEqual(listing.expires_at, expected_max)

    def test_listing_default_values(self):
        """Test listing has correct default values"""
        listing = Listing.objects.create(
            user=self.user,
            type=Listing.TYPE_FOUND,
            title="Test",
            description="Test",
        )

        self.assertEqual(listing.status, Listing.STATUS_ACTIVE)
        self.assertEqual(listing.gender, Listing.GENDER_UNKNOWN)
        self.assertFalse(listing.has_collar)
        self.assertEqual(listing.search_radius_km, 5)

    def test_is_active_property(self):
        """Test is_active property returns correct value"""
        listing = Listing.objects.create(
            user=self.user,
            type=Listing.TYPE_FOUND,
            title="Test",
            description="Test",
        )

        self.assertTrue(listing.is_active)

        listing.status = Listing.STATUS_EXPIRED
        self.assertFalse(listing.is_active)

    def test_is_expired_property(self):
        """Test is_expired property checks expiration correctly"""
        listing = Listing.objects.create(
            user=self.user,
            type=Listing.TYPE_FOUND,
            title="Test",
            description="Test",
        )

        self.assertFalse(listing.is_expired)

        listing.expires_at = timezone.now() - timedelta(hours=1)
        self.assertTrue(listing.is_expired)

    def test_search_radius_validation_min(self):
        """Test search_radius_km cannot be less than 1"""
        listing = Listing.objects.create(
            user=self.user,
            type=Listing.TYPE_FOUND,
            title="Test",
            description="Test",
            search_radius_km=0,
        )

        with self.assertRaises(ValidationError):
            listing.full_clean()

    def test_search_radius_validation_max(self):
        """Test search_radius_km cannot be more than 10"""
        listing = Listing.objects.create(
            user=self.user,
            type=Listing.TYPE_FOUND,
            title="Test",
            description="Test",
            search_radius_km=11,
        )

        with self.assertRaises(ValidationError):
            listing.full_clean()

    def test_str_method(self):
        """Test __str__ method returns correct string"""
        listing = Listing.objects.create(
            user=self.user,
            type=Listing.TYPE_FOUND,
            title="Found Golden Retriever",
            description="Test",
        )

        self.assertEqual(str(listing), "Found Dog: Found Golden Retriever")


class PhotoModelTests(TestCase):
    """Tests for Photo model"""

    def setUp(self):
        """Create test user and listing"""
        self.user = create_user()
        self.listing = Listing.objects.create(
            user=self.user,
            type=Listing.TYPE_FOUND,
            title="Test Listing",
            description="Test",
        )

    def test_create_photo_successful(self):
        """Test creating a photo for listing"""
        photo = Photo.objects.create(
            listing=self.listing,
            cloudinary_url="https://res.cloudinary.com/test/image.jpg",
            cloudinary_public_id="test/image",
            order_index=0,
        )

        self.assertEqual(photo.listing, self.listing)
        self.assertEqual(photo.order_index, 0)
        self.assertIn("cloudinary.com", photo.cloudinary_url)

    def test_photo_default_order_index(self):
        """Test photo has default order_index of 0"""
        photo = Photo.objects.create(
            listing=self.listing,
            cloudinary_url="https://res.cloudinary.com/test/image.jpg",
        )

        self.assertEqual(photo.order_index, 0)

    def test_multiple_photos_ordering(self):
        """Test multiple photos are ordered correctly"""
        photo1 = Photo.objects.create(
            listing=self.listing,
            cloudinary_url="https://res.cloudinary.com/test/image1.jpg",
            order_index=1,
        )
        photo2 = Photo.objects.create(
            listing=self.listing,
            cloudinary_url="https://res.cloudinary.com/test/image2.jpg",
            order_index=0,
        )

        photos = self.listing.photos.all()
        self.assertEqual(photos[0], photo2)
        self.assertEqual(photos[1], photo1)

    def test_str_method(self):
        """Test __str__ method returns correct string"""
        photo = Photo.objects.create(
            listing=self.listing,
            cloudinary_url="https://res.cloudinary.com/test/image.jpg",
            order_index=0,
        )

        self.assertEqual(str(photo), "Photo 1 for Test Listing")


class LocationModelTests(TestCase):
    """Tests for Location model"""

    def setUp(self):
        """Create test user and listing"""
        self.user = create_user()
        self.listing = Listing.objects.create(
            user=self.user,
            type=Listing.TYPE_FOUND,
            title="Test Listing",
            description="Test",
        )

    def test_create_location_successful(self):
        """Test creating a location for listing"""
        point = Point(22.5684, 51.2465)

        location = Location.objects.create(
            listing=self.listing,
            added_by_user=self.user,
            point=point,
            address="Test Address, Lublin",
        )

        self.assertEqual(location.listing, self.listing)
        self.assertEqual(location.added_by_user, self.user)
        self.assertIsNotNone(location.point)
        self.assertTrue(location.is_primary)

    def test_location_auto_populates_lat_lng(self):
        """Test latitude/longitude are auto-populated from point"""
        point = Point(22.5684, 51.2465)

        location = Location.objects.create(
            listing=self.listing,
            point=point,
        )

        self.assertIsNotNone(location.latitude)
        self.assertIsNotNone(location.longitude)
        self.assertAlmostEqual(float(location.longitude), 22.5684, places=4)
        self.assertAlmostEqual(float(location.latitude), 51.2465, places=4)

    def test_only_one_primary_location_per_listing(self):
        """Test only one location can be primary per listing"""
        point1 = Point(22.5684, 51.2465)
        point2 = Point(22.5700, 51.2500)

        location1 = Location.objects.create(
            listing=self.listing,
            point=point1,
            is_primary=True,
        )

        location2 = Location.objects.create(
            listing=self.listing,
            point=point2,
            is_primary=True,
        )

        location1.refresh_from_db()

        self.assertFalse(location1.is_primary)
        self.assertTrue(location2.is_primary)

    def test_location_default_values(self):
        """Test location has correct default values"""
        point = Point(22.5684, 51.2465)

        location = Location.objects.create(
            listing=self.listing,
            point=point,
        )

        self.assertTrue(location.is_primary)
        self.assertEqual(location.location_type, Location.TYPE_EXACT)
        self.assertEqual(location.area_radius_meters, 0)

    def test_str_method(self):
        """Test __str__ method returns correct string"""
        point = Point(22.5684, 51.2465)

        location = Location.objects.create(
            listing=self.listing,
            point=point,
            is_primary=True,
        )

        self.assertEqual(str(location), "Location for Test Listing (Primary)")

    def test_str_method_non_primary(self):
        """Test __str__ for non-primary location"""
        point = Point(22.5684, 51.2465)

        location = Location.objects.create(
            listing=self.listing,
            point=point,
            is_primary=False,
        )

        self.assertEqual(str(location), "Location for Test Listing")
