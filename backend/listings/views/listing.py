from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import viewsets, filters, status
from rest_framework.permissions import (
    IsAuthenticated,
    IsAuthenticatedOrReadOnly,
)
from ..permissions import IsOwnerOrReadOnly
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from django.contrib.gis.geos import Point
from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.measure import D

import cloudinary.uploader

from ..models import Listing, Location, Photo
from ..serializers import (
    ListingSerializer,
    PhotoSerializer,
    PhotoUploadSerializer,
    LocationSerializer,
    SimilarListingSerializer,
    ListingListSerializer,
)
from ..schemas import (
    listing_viewset_schema,
    mark_found_schema,
    nearby_schema,
    upload_photo_schema,
    delete_photo_schema,
    add_location_schema,
    delete_location_schema,
    check_similar_schema,
)
from ..services import DuplicateDetector
from listings.filters import ListingFilter

from chats.models import Conversation, ConversationMembership
from chats.serializers import ConversationSerializer


@listing_viewset_schema
class ListingViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing dog listings (lost and found).

    Provides CRUD operations and special actions:
    - List/Create/Update/Delete listings
    - Search nearby listings by location
    - Mark listings as found/returned
    """

    queryset = Listing.objects.all().order_by("-created_at")
    serializer_class = ListingSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]

    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_class = ListingFilter
    search_fields = ["title", "description", "dog_name"]

    def perform_create(self, serializer):
        """Automatically set the listing owner to the current user"""
        serializer.save(user=self.request.user)

    def get_serializer_class(self):
        if self.action == "list":
            return ListingListSerializer
        return ListingSerializer

    @mark_found_schema
    @action(detail=True, methods=["post"])
    def mark_found(self, request, pk=None):
        """
        Mark a listing as found/returned.
        Only the listing owner can mark their own listing.
        """
        listing = self.get_object()

        if listing.type == "lost":
            listing.status = Listing.STATUS_FOUND
        else:  # found
            listing.status = Listing.STATUS_RETURNED

        listing.save()

        serializer = self.get_serializer(listing)
        return Response(serializer.data)

    @nearby_schema
    @action(detail=False, methods=["get"], url_path="nearby")
    def nearby(self, request):
        """
        Find listings near a location.

        Query params:
        - latitude (required)
        - longitude (required)
        - radius_km (optional, default 5)
        - type (optional: 'lost' or 'found')
        """
        lat = request.query_params.get("latitude")
        lng = request.query_params.get("longitude")
        radius_km = request.query_params.get("radius_km", 5)
        listing_type = request.query_params.get("type")

        if not lat or not lng:
            return Response(
                {"error": "latitude and longitude are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            lat = float(lat)
            lng = float(lng)
            radius_km = float(radius_km)
        except ValueError:
            return Response(
                {"error": "Invalid coordinates or radius"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if radius_km > 10:
            radius_km = 10

        user_location = Point(lng, lat, srid=4326)

        queryset = (
            Listing.objects.filter(
                locations__is_primary=True,
                locations__point__distance_lte=(
                    user_location,
                    D(km=radius_km),
                ),
            )
            .annotate(distance=Distance("locations__point", user_location))
            .order_by("distance")
        )

        if listing_type:
            queryset = queryset.filter(type=listing_type)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @upload_photo_schema
    @action(detail=True, methods=["post"])
    def upload_photo(self, request, pk=None):
        """
        Upload photo for a listing.
        Only the listing owner can add photo for their own listing.
        """
        listing = self.get_object()

        data = request.data.copy()
        data["listing"] = listing.id

        serializer = PhotoUploadSerializer(data=data)
        serializer.is_valid(raise_exception=True)

        photo = serializer.save()

        return Response(
            PhotoSerializer(photo).data, status=status.HTTP_201_CREATED
        )

    @delete_photo_schema
    @action(
        detail=True, methods=["delete"], url_path="photos/(?P<photo_id>[^/.]+)"
    )
    def delete_photo(self, request, pk=None, photo_id=None):
        """
        Delete a photo from listing.
        Only the listing owner can delete photos.
        """
        listing = self.get_object()

        try:
            photo = listing.photos.get(id=photo_id)
        except Photo.DoesNotExist:
            return Response(
                {"error": "Photo not found in this listing"},
                status=status.HTTP_404_NOT_FOUND,
            )

        photo_id_deleted = photo.id
        cloudinary_public_id = photo.cloudinary_public_id

        try:
            if cloudinary_public_id:
                cloudinary.uploader.destroy(cloudinary_public_id)

            photo.delete()

            return Response(
                {
                    "id": photo_id_deleted,
                    "message": "Photo deleted successfully",
                    "deleted_at": timezone.now(),
                },
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            return Response(
                {"error": f"Failed to delete photo: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @add_location_schema
    @action(
        detail=True,
        methods=["post"],
        url_path="location",
        permission_classes=[IsAuthenticated],
    )
    def add_location(self, request, pk=None):
        listing = self.get_object()

        serializer = LocationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        location = serializer.save(added_by_user=request.user, listing=listing)

        return Response(
            LocationSerializer(location).data, status=status.HTTP_201_CREATED
        )

    @delete_location_schema
    @action(
        detail=True,
        methods=["delete"],
        url_path="locations/(?P<location_id>[^/.]+)",
    )
    def delete_location(self, request, pk=None, location_id=None):
        """
        Delete a specific location from this listing.
        Only the listing owner or the user who added
        the location can delete it.
        """
        listing = get_object_or_404(Listing, pk=pk)
        location = get_object_or_404(Location, id=location_id, listing=listing)

        if request.user not in (listing.user, location.added_by_user):
            return Response(
                {
                    "detail": (
                        "You do not have permission to perform this action."
                    )
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        location_id_deleted = location.id
        was_primary = location.is_primary
        location.delete()

        if was_primary:
            new_primary = listing.locations.order_by("-created_at").first()
            if new_primary:
                new_primary.is_primary = True
                new_primary.save()

        return Response(
            {
                "id": location_id_deleted,
                "message": "Location deleted successfully",
                "deleted_at": timezone.now(),
            },
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["get"], url_path="chat")
    def chat(self, request, pk=None):
        listing = self.get_object()
        conversation = get_object_or_404(Conversation, listing=listing)
        ConversationMembership.objects.get_or_create(
            user=request.user, conversation=conversation
        )
        return Response(ConversationSerializer(conversation).data)

    @check_similar_schema
    @action(detail=False, methods=["post"], url_path="check-similar")
    def check_similar(self, request):
        """
        Find similar listings based on characteristics and location.
        """
        serializer = SimilarListingSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        validated_data = serializer.validated_data

        search_type = validated_data.pop("search_type")

        detector = DuplicateDetector(radius_km=2)
        similar_listings = detector.find_similar_listings(
            listing_data=validated_data, listing_type=search_type
        )

        return Response(
            ListingSerializer(similar_listings, many=True).data,
            status=status.HTTP_200_OK,
        )
