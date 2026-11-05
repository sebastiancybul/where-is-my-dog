from rest_framework import serializers

from chats.models import Conversation

from .message import MessageSerializer


class ConversationSerializer(serializers.ModelSerializer):
    last_message = serializers.SerializerMethodField()
    listing_title = serializers.SerializerMethodField()
    listing_photo = serializers.SerializerMethodField()
    other_participant = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = [
            "id",
            "type",
            "listing_id",
            "listing_title",
            "listing_photo",
            "is_closed",
            "last_message",
            "other_participant",
            "created_at",
        ]

    def get_last_message(self, obj):
        if hasattr(obj, "latest_messages"):
            message = next(iter(obj.latest_messages), None)
        else:
            message = obj.messages.order_by("-created_at", "-id").first()
        if not message:
            return None
        return MessageSerializer(message).data

    def get_listing_title(self, obj):
        return obj.listing.title if obj.listing else None

    def get_listing_photo(self, obj):
        if not obj.listing:
            return None
        photo = next(iter(obj.listing.photos.all()), None)
        return photo.thumbnail_url if photo else None

    def get_other_participant(self, obj):
        request = self.context.get("request")
        if not request:
            return None
        other = next(
            (
                m
                for m in obj.memberships.all()
                if m.user_id != request.user.id
            ),
            None,
        )
        if not other:
            return None
        user = other.user
        return {
            "id": user.id,
            "username": user.username,
            "profile_photo": (
                user.profile_photo.url if user.profile_photo else None
            ),
        }
