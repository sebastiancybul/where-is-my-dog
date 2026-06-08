from rest_framework import serializers

from ..models import Listing
from . import PhotoSerializer, LocationSerializer
from users.serializers import UserPublicSerializer

from rest_framework_gis.fields import GeometryField

from chats.models import Conversation


class ListingListSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for Listing model used in list views.
    Includes only essential fields.
    """

    primary_photo = serializers.SerializerMethodField()
    primary_location = serializers.SerializerMethodField()

    class Meta:
        model = Listing
        fields = (
            "id",
            "type",
            "status",
            "title",
            "reward_offered",
            "primary_photo",
            "dog_name",
            "primary_location",
            "description",
            "breed",
            "age_estimate",
            "color",
            "has_collar",
            "collar_color",
            "created_at",
        )

    def get_primary_location(self, obj):
        """
        Returns the primary (most recent) location for this listing.
        """
        primary = obj.locations.filter(is_primary=True).first()
        if primary:
            return primary.address
        return None

    def get_primary_photo(self, obj):
        photo = obj.photos.order_by("order_index").first()
        if photo:
            return photo.thumbnail_url
        return None


class ListingSerializer(serializers.ModelSerializer):
    """
    Main serializer for Listing model.
    Includes nested photos and locations.
    """

    photos = PhotoSerializer(many=True, read_only=True)
    locations = LocationSerializer(many=True, read_only=True)
    user = UserPublicSerializer(read_only=True)

    primary_location = serializers.SerializerMethodField()
    photo_count = serializers.SerializerMethodField()
    public_conversation_id = serializers.SerializerMethodField()
    public_conversation_is_closed = serializers.SerializerMethodField()

    class Meta:
        model = Listing
        fields = (
            "id",
            "user",
            "type",
            "status",
            "title",
            "description",
            "breed",
            "size",
            "color",
            "gender",
            "has_collar",
            "collar_color",
            "dog_name",
            "age_estimate",
            "special_marks",
            "fostering_address",
            "reward_offered",
            "search_radius_km",
            "photos",
            "photo_count",
            "locations",
            "primary_location",
            "public_conversation_id",
            "public_conversation_is_closed",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "created_at",
            "updated_at",
        )

    def get_primary_location(self, obj):
        """
        Returns the primary (most recent) location for this listing.
        """
        primary = obj.locations.filter(is_primary=True).first()
        if primary:
            return LocationSerializer(primary).data
        return None

    def get_photo_count(self, obj):
        """
        Returns the total number of photos for this listing.
        """
        return obj.photos.count()

    def validate_search_radius_km(self, value):
        """
        Custom validation for search radius.
        For Lublin area, we limit radius to 1-10 km.
        """
        if value < 1 or value > 10:
            raise serializers.ValidationError(
                "Search radius must be between 1 and 10 km for Lublin area"
            )
        return value

    def get_public_conversation(self, obj):
        return obj.conversations.filter(type=Conversation.TYPE_PUBLIC).first()

    def get_public_conversation_id(self, obj):
        conv = self.get_public_conversation(obj)
        return conv.pk if conv else None

    def get_public_conversation_is_closed(self, obj):
        conv = self.get_public_conversation(obj)
        return conv.is_closed if conv else None


class SimilarListingSerializer(serializers.Serializer):
    """
    Serializer for duplicate detection request.
    """

    search_type = serializers.ChoiceField(
        choices=["found", "lost"],
        help_text="Type of listings to search: 'found' or 'lost'",
    )
    point = GeometryField(help_text="Geographic location (GeoJSON Point)")
    breed = serializers.CharField(max_length=100, help_text="Dog breed")
    size = serializers.ChoiceField(
        choices=["small", "medium", "large"], help_text="Dog size"
    )
    has_collar = serializers.BooleanField(help_text="Whether dog has a collar")
    collar_color = serializers.CharField(
        max_length=50,
        required=False,
        allow_blank=True,
        help_text="Collar color (only if has_collar=True)",
    )

    def validate(self, data):
        """
        Check that collar_color is provided if has_collar=True
        """
        if data["has_collar"] and not data.get("collar_color"):
            raise serializers.ValidationError(
                {
                    "collar_color": (
                        "Collar color is required when " "has_collar=True"
                    )
                }
            )
        return data
