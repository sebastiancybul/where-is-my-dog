from datetime import timedelta
from django.db import models
from django.conf import settings
from django.contrib.gis.db import models as gis_models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone

from cloudinary.models import CloudinaryField


class Listing(models.Model):
    """
    Main listing model for lost or found dogs.
    """

    # Listings types
    TYPE_LOST = "lost"
    TYPE_FOUND = "found"
    TYPE_CHOICES = [
        (TYPE_LOST, "Lost Dog"),
        (TYPE_FOUND, "Found Dog"),
    ]

    # Listings statuses
    STATUS_ACTIVE = "active"
    STATUS_EXPIRED = "expired"
    STATUS_FOUND = "found"
    STATUS_RETURNED = "returned"
    STATUS_CHOICES = [
        (STATUS_ACTIVE, "Active"),
        (STATUS_EXPIRED, "Expired"),
        (STATUS_FOUND, "Found"),
        (STATUS_RETURNED, "Returned to Owner"),
    ]

    # Dog sizes
    SIZE_SMALL = "small"
    SIZE_MEDIUM = "medium"
    SIZE_LARGE = "large"
    SIZE_CHOICES = [
        (SIZE_SMALL, "Small (up to 10kg)"),
        (SIZE_MEDIUM, "Medium (10-25kg)"),
        (SIZE_LARGE, "Large (25kg+)"),
    ]

    # Dog genders
    GENDER_MALE = "male"
    GENDER_FEMALE = "female"
    GENDER_UNKNOWN = "unknown"
    GENDER_CHOICES = [
        (GENDER_MALE, "Male"),
        (GENDER_FEMALE, "Female"),
        (GENDER_UNKNOWN, "Unknown"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="listings",
        help_text="User who created this listing",
    )

    type = models.CharField(
        max_length=10,
        choices=TYPE_CHOICES,
        help_text="Whether this is a lost or found dog listing",
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_ACTIVE,
        help_text="Current status of the listing",
    )

    title = models.CharField(
        max_length=200, help_text="Brief title for the listing"
    )

    description = models.TextField(
        help_text="Detailed description of the dog and circumstances"
    )

    breed = models.CharField(
        max_length=100, blank=True, null=True, help_text="Dog breed (if known)"
    )

    size = models.CharField(
        max_length=10,
        choices=SIZE_CHOICES,
        blank=True,
        null=True,
        help_text="Approximate size of the dog",
    )

    color = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Primary color of the dog",
    )

    gender = models.CharField(
        max_length=10,
        choices=GENDER_CHOICES,
        default=GENDER_UNKNOWN,
        help_text="Dog's gender (if known)",
    )

    has_collar = models.BooleanField(
        default=False, help_text="Whether the dog has a collar"
    )

    collar_color = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Color of the collar (if present)",
    )

    dog_name = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Dog's name (if known)",
    )

    age_estimate = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        help_text="Estimated age (e.g., 'puppy', '2 years', 'senior')",
    )

    microchip_number = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Microchip number (if known)",
    )

    special_marks = models.TextField(
        blank=True,
        null=True,
        help_text="Any distinctive marks, scars, or features",
    )

    reward_offered = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        validators=[MinValueValidator(0)],
        help_text="Reward amount (if any)",
    )

    fostering_address = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Address where dog is being fostered (if applicable)",
    )

    search_radius_km = models.IntegerField(
        default=5,
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        help_text="Search radius in kilometers (1-10km)",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField(
        blank=True, null=True, help_text="When this listing expires"
    )

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Listing"
        verbose_name_plural = "Listings"

    def __str__(self):
        return f"{self.get_type_display()}: {self.title}"

    def save(self, *args, **kwargs):
        """Auto-set exipres_at for new 'found' listings"""

        is_new = self.pk is None

        if is_new and self.status == self.STATUS_ACTIVE:
            if self.type == self.TYPE_FOUND:
                self.expires_at = timezone.now() + timedelta(days=2)
            elif self.type == self.TYPE_LOST:
                self.expires_at = timezone.now() + timedelta(days=5)

        super().save(*args, **kwargs)

    @property
    def is_active(self):
        """Check if listing is currently active"""
        return self.status == self.STATUS_ACTIVE

    @property
    def is_expired(self):
        """Check if listing has expired"""
        from django.utils import timezone

        if self.expires_at:
            return timezone.now() > self.expires_at
        return False


class Photo(models.Model):
    """
    Photos associated with a listing.
    Maximum 2 photos per listing.
    """

    listing = models.ForeignKey(
        Listing,
        on_delete=models.CASCADE,
        related_name="photos",
        help_text="Listing this photo belongs to",
    )

    cloudinary_url = CloudinaryField(
        "photo",
        folder="listings/photos",
        help_text="Photo stored in Cloudinary",
    )

    cloudinary_public_id = models.CharField(
        max_length=255, blank=True, help_text="Cloudinary public ID"
    )

    thumbnail_url = models.CharField(
        max_length=500, blank=True, help_text="Thumbnail URL"
    )

    order_index = models.IntegerField(
        default=0, help_text="Order of photo display (0 = primary)"
    )

    file_size = models.IntegerField(
        blank=True, null=True, help_text="File size in bytes"
    )

    width = models.IntegerField(
        blank=True, null=True, help_text="Image width in pixels"
    )

    height = models.IntegerField(
        blank=True, null=True, help_text="Image height in pixels"
    )

    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["order_index", "uploaded_at"]
        verbose_name = "Photo"
        verbose_name_plural = "Photos"

    def __str__(self):
        return f"Photo {self.order_index + 1} for {self.listing.title}"


class Location(models.Model):
    """
    Geographic locations associated with listings.
    Uses PostGIS for geospatial queries.
    Supports location history (multiple locations per listing).
    """

    TYPE_EXACT = "exact"
    TYPE_APPROXIMATE = "approximate"
    TYPE_CHOICES = [
        (TYPE_EXACT, "Exact Location"),
        (TYPE_APPROXIMATE, "Approximate Area"),
    ]

    listing = models.ForeignKey(
        Listing,
        on_delete=models.CASCADE,
        related_name="locations",
        help_text="Listing this location belongs to",
    )

    added_by_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="added_locations",
        help_text="User who added this location update",
    )

    point = gis_models.PointField(
        geography=True,
        help_text="Geographic coordinates (longitude, latitude)",
    )

    latitude = models.DecimalField(
        max_digits=10,
        decimal_places=8,
        blank=True,
        null=True,
        help_text="Latitude coordinate",
    )

    longitude = models.DecimalField(
        max_digits=11,
        decimal_places=8,
        blank=True,
        null=True,
        help_text="Longitude coordinate",
    )

    area_radius_meters = models.IntegerField(
        default=0, help_text="Radius for approximate locations (meters)"
    )

    address = models.CharField(
        max_length=500,
        blank=True,
        null=True,
        help_text="Human-readable address",
    )

    location_type = models.CharField(
        max_length=15,
        choices=TYPE_CHOICES,
        default=TYPE_EXACT,
        help_text="Exact or approximate location",
    )

    is_primary = models.BooleanField(
        default=True,
        help_text="Whether this is the primary/most recent location",
    )

    notes = models.TextField(
        blank=True, null=True, help_text="Additional notes about this location"
    )

    accuracy_meters = models.IntegerField(
        blank=True, null=True, help_text="GPS accuracy in meters"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Location"
        verbose_name_plural = "Locations"

    def __str__(self):
        primary = " (Primary)" if self.is_primary else ""
        return f"Location for {self.listing.title}{primary}"

    def save(self, *args, **kwargs):
        """
        Auto-populate latitude/longitude from point field.
        Ensure only one primary location per listing.
        """

        if self.point:
            self.longitude = self.point.x
            self.latitude = self.point.y

        if self.is_primary:
            Location.objects.filter(
                listing=self.listing, is_primary=True
            ).exclude(pk=self.pk).update(is_primary=False)

        super().save(*args, **kwargs)
