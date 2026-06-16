from rest_framework import serializers

from .models import DeviceToken, Notification


class DeviceTokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeviceToken
        fields = ("token", "platform")
        extra_kwargs = {"token": {"validators": []}}


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = (
            "id",
            "event_type",
            "title",
            "body",
            "data",
            "is_read",
            "created_at",
        )
        read_only_fields = fields
