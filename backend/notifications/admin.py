from django.contrib import admin
from .models import DeviceToken


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
