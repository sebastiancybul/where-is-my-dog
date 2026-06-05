from django.contrib import admin
from .models import Listing, Photo, Location


@admin.register(Listing)
class ListingAdmin(admin.ModelAdmin):
    """Basic admin for Listing model"""

    list_display = (
        "title",
        "type",
        "status",
        "user",
        "breed",
        "created_at",
    )

    list_filter = (
        "type",
        "status",
        "size",
        "gender",
        "has_collar",
        "created_at",
    )

    search_fields = (
        "title",
        "description",
        "breed",
        "dog_name",
        "microchip_number",
    )

    ordering = ("-created_at",)

    readonly_fields = ("created_at", "updated_at")


@admin.register(Photo)
class PhotoAdmin(admin.ModelAdmin):
    """Basic admin for Photo model"""

    list_display = (
        "listing",
        "order_index",
        "uploaded_at",
    )

    list_filter = ("uploaded_at",)

    ordering = ("listing", "order_index")

    readonly_fields = ("uploaded_at",)


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    """Basic admin for Location model"""

    list_display = (
        "listing",
        "location_type",
        "is_primary",
        "added_by_user",
        "created_at",
    )

    list_filter = (
        "location_type",
        "is_primary",
        "created_at",
    )

    search_fields = (
        "address",
        "notes",
    )

    ordering = ("-created_at",)

    readonly_fields = ("created_at", "latitude", "longitude")
