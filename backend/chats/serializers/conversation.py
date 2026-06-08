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
        message = obj.messages.last()
        if not message:
            return None
        return MessageSerializer(message).data

    def get_listing_title(self, obj):
        return obj.listing.title if obj.listing else None

    def get_listing_photo(self, obj):
        if not obj.listing:
            return None
        photo = obj.listing.photos.order_by("order_index").first()
        return photo.thumbnail_url if photo else None

    def get_other_participant(self, obj):
        request = self.context.get("request")
        if not request:
            return None
        other = (
            obj.memberships.exclude(user=request.user)
            .select_related("user")
            .first()
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
