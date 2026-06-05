from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    Admin configuration for custom User model.
    Extends Django's default UserAdmin with custom fields.
    """

    # Fields to display in user list
    list_display = (
        "username",
        "email",
        "phone",
        "email_verified",
        "is_moderator",
        "is_banned",
        "is_staff",
        "is_active",
        "created_at",
    )

    # Filters in sidebar
    list_filter = (
        "is_staff",
        "is_active",
        "is_moderator",
        "is_banned",
        "email_verified",
        "created_at",
    )

    # Search fields
    search_fields = (
        "username",
        "email",
        "phone",
        "first_name",
        "last_name",
    )

    # Order by newest first
    ordering = ("-created_at",)

    # Fields shown when editing user
    fieldsets = (
        (None, {"fields": ("username", "password")}),
        (
            "Personal info",
            {
                "fields": (
                    "first_name",
                    "last_name",
                    "email",
                    "phone",
                    "profile_photo",
                )
            },
        ),
        (
            "Verification & Status",
            {
                "fields": (
                    "email_verified",
                    "is_active",
                    "is_banned",
                )
            },
        ),
        (
            "Permissions",
            {
                "fields": (
                    "is_staff",
                    "is_superuser",
                    "is_moderator",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        (
            "Important dates",
            {
                "fields": (
                    "last_login",
                    "created_at",
                    "updated_at",
                )
            },
        ),
    )

    # Fields shown when creating new user
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "username",
                    "email",
                    "phone",
                    "password1",
                    "password2",
                    "is_staff",
                    "is_moderator",
                ),
            },
        ),
    )

    # Read-only fields
    readonly_fields = (
        "created_at",
        "updated_at",
        "last_login",
    )
