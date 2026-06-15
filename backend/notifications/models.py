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
