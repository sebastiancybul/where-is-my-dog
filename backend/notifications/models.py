from django.conf import settings
from django.db import models


class DeviceToken(models.Model):
    """
    FCM registration token for a user's device.
    One user can have many tokens (multiple devices).
    """

    PLATFORM_IOS = "ios"
    PLATFORM_ANDROID = "android"
    PLATFORM_CHOICES = [
        (PLATFORM_IOS, "iOS"),
        (PLATFORM_ANDROID, "Android"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="device_tokens",
        help_text="User this device belongs to",
    )

    token = models.CharField(
        max_length=500,
        unique=True,
        help_text="FCM registration token for the device",
    )

    platform = models.CharField(
        max_length=10,
        choices=PLATFORM_CHOICES,
        help_text="Device platform",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Device Token"
        verbose_name_plural = "Device Tokens"

    def __str__(self):
        return f"{self.user} ({self.platform})"


class Notification(models.Model):
    """
    Persisted in-app notification for non-chat events
    (e.g. inquiry about your listing, new location reported).
    Shown in the notification inbox; chat messages are not stored here.
    """

    EVENT_LISTING_INQUIRY = "listing_inquiry"
    EVENT_LISTING_AUTHOR_CONTACT = "listing_author_contact"
    EVENT_LOCATION_REPORTED = "location_reported"
    EVENT_LISTING_EXPIRING = "listing_expiring"
    EVENT_LISTING_EXPIRED = "listing_expired"
    EVENT_LISTING_RESOLVED = "listing_resolved"
    EVENT_NEARBY_LISTING = "nearby_listing"
    EVENT_TYPE_CHOICES = [
        (EVENT_LISTING_INQUIRY, "Listing inquiry"),
        (EVENT_LISTING_AUTHOR_CONTACT, "Listing author contact"),
        (EVENT_LOCATION_REPORTED, "Location reported"),
        (EVENT_LISTING_EXPIRING, "Listing expiring soon"),
        (EVENT_LISTING_EXPIRED, "Listing expired"),
        (EVENT_LISTING_RESOLVED, "Listing resolved"),
        (EVENT_NEARBY_LISTING, "Nearby listing"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
        help_text="Recipient of the notification",
    )

    event_type = models.CharField(
        max_length=50,
        choices=EVENT_TYPE_CHOICES,
        help_text="What kind of event triggered this notification",
    )

    title = models.CharField(max_length=255)
    body = models.TextField(blank=True)

    data = models.JSONField(
        default=dict,
        blank=True,
        help_text="Extra payload for deep-linking (e.g. listing_id)",
    )

    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Notification"
        verbose_name_plural = "Notifications"

    def __str__(self):
        return f"{self.event_type} -> {self.user}"
