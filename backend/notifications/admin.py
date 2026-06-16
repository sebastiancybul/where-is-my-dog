from django.contrib import admin
from .models import DeviceToken, Notification


@admin.register(DeviceToken)
class DeviceTokenAdmin(admin.ModelAdmin):
    """Basic admin for DeviceToken model"""

    list_display = (
        "user",
        "platform",
        "created_at",
        "updated_at",
    )

    list_filter = (
        "platform",
        "created_at",
    )

    search_fields = (
        "user__username",
        "user__email",
        "token",
    )

    ordering = ("-created_at",)

    readonly_fields = ("created_at", "updated_at")


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    """Basic admin for Notification model"""

    list_display = (
        "user",
        "event_type",
        "title",
        "is_read",
        "created_at",
    )

    list_filter = (
        "event_type",
        "is_read",
        "created_at",
    )

    search_fields = (
        "user__username",
        "user__email",
        "title",
        "body",
    )

    ordering = ("-created_at",)

    readonly_fields = ("created_at",)
