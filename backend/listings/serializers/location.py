from rest_framework import serializers
from rest_framework_gis.fields import GeometryField
from ..models import Location


class LocationSerializer(serializers.ModelSerializer):
    """
    Serializer for Location model.
    Handles geographic data for listings.
    """

    point = GeometryField()

    class Meta:
        model = Location
        fields = (
            "id",
            "added_by_user",
            "listing",
            "latitude",
            "longitude",
            "point",
            "address",
            "location_type",
            "is_primary",
            "notes",
            "accuracy_meters",
            "created_at",
        )
        read_only_fields = (
            "id",
            "listing",
            "created_at",
            "added_by_user",
            "latitude",
            "longitude",
        )
