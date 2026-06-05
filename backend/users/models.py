from django.contrib.auth.models import AbstractUser
from django.db import models
from cloudinary.models import CloudinaryField


class User(AbstractUser):
    """
    Custom User model for Where Is My Dog application.
    Extends Django's AbstractUser with additional fields for profile and moderation.
    """  # noqa

    email = models.EmailField(
        max_length=255,
        unique=True,
        blank=False,
        help_text="Email address - used for notifications and verification",
    )

    phone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        help_text="User phone number for contact",
    )

    # Profile photo stored in Cloudinary
    profile_photo = CloudinaryField(
        "profile",
        blank=True,
        null=True,
        folder="users/profiles",
        help_text="User profile photo",
    )

    # Email verification status
    email_verified = models.BooleanField(
        default=False, help_text="Whether the user's email has been verified"
    )

    # User roles and moderation
    is_moderator = models.BooleanField(
        default=False, help_text="Designates whether user can moderate content"
    )

    is_banned = models.BooleanField(
        default=False,
        help_text="Designates whether user is banned from the platform",
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Note: last_login is already provided by AbstractUser
    # Note: is_active, is_staff are already provided by AbstractUser

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "User"
        verbose_name_plural = "Users"

    def __str__(self):
        return self.username

    @property
    def full_name(self):
        """Returns user's full name or username if not set"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.username
