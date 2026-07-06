from drf_spectacular.utils import (
    extend_schema,
    OpenApiParameter,
    OpenApiResponse,
    OpenApiExample,
)

from .serializers import (
    ListingSerializer,
    PhotoSerializer,
    PhotoDeleteSerializer,
    LocationSerializer,
    SimilarListingSerializer,
)

listing_viewset_schema = extend_schema(tags=["Listings"])

mark_found_schema = extend_schema(
    summary="Mark listing as found/returned",
    description=(
        "Mark a listing as found (for lost dogs) or returned to owner "
        "(for found dogs). Only the listing owner can perform this action."
    ),
    request=None,
    responses={
        200: ListingSerializer,
        403: OpenApiResponse(
            description="Not the owner of this listing",
            examples=[
                OpenApiExample(
                    "Forbidden",
                    value={
                        "detail": "You do not have permission to perform this action."
                    },
                )
            ],
        ),
    },
)

bump_schema = extend_schema(
    summary="Bump (renew) a listing",
    description=(
        "Reset the listing's expiry window to the default for its type "
        "and clear the 'expiring soon' guard. Only the owner can bump, "
        "and only while the listing is active."
    ),
    request=None,
    responses={
        200: ListingSerializer,
        400: OpenApiResponse(
            description="Listing is not active",
            examples=[
                OpenApiExample(
                    "Not active",
                    value={"detail": "Only active listings can be bumped."},
                )
            ],
        ),
        403: OpenApiResponse(
            description="Not the owner of this listing",
            examples=[
                OpenApiExample(
                    "Forbidden",
                    value={
                        "detail": "You do not have permission to perform this action."
                    },
                )
            ],
        ),
    },
)

nearby_schema = extend_schema(
    summary="Find listings near a location",
    description=(
        "Search for lost or found dog listings within a specified radius "
        "of a geographic location. Results are ordered by distance (closest first)."
    ),
    parameters=[
        OpenApiParameter(
            name="latitude",
            type=float,
            location=OpenApiParameter.QUERY,
            required=True,
            description="Latitude coordinate (e.g., 51.2465 for Lublin)",
            examples=[OpenApiExample("Lublin", value=51.2465)],
        ),
        OpenApiParameter(
            name="longitude",
            type=float,
            location=OpenApiParameter.QUERY,
            required=True,
            description="Longitude coordinate (e.g., 22.5684 for Lublin)",
            examples=[OpenApiExample("Lublin", value=22.5684)],
        ),
        OpenApiParameter(
            name="radius_km",
            type=float,
            location=OpenApiParameter.QUERY,
            required=False,
            description="Search radius in kilometers (default: 5, max: 10)",
            examples=[OpenApiExample("Default", value=5)],
        ),
        OpenApiParameter(
            name="type",
            type=str,
            location=OpenApiParameter.QUERY,
            required=False,
            description="Filter by listing type",
            enum=["lost", "found"],
        ),
    ],
    responses={
        200: ListingSerializer(many=True),
        400: OpenApiResponse(
            description="Invalid parameters",
            examples=[
                OpenApiExample(
                    "Missing coordinates",
                    value={"error": "latitude and longitude are required"},
                ),
                OpenApiExample(
                    "Invalid format",
                    value={"error": "Invalid coordinates or radius"},
                ),
            ],
        ),
    },
)

upload_photo_schema = extend_schema(
    summary="Upload photo for listing",
    description=(
        "Upload a photo to this listing. The photo will be uploaded to Cloudinary "
        "and a thumbnail will be automatically generated. Maximum 2 photos per listing."
    ),
    request={
        "multipart/form-data": {
            "type": "object",
            "properties": {
                "photo": {
                    "type": "string",
                    "format": "binary",
                    "description": "Photo file (JPEG, PNG, WebP, max 5MB)",
                },
                "order_index": {
                    "type": "integer",
                    "default": 0,
                    "description": "Order of photo display (0 = primary)",
                },
            },
            "required": ["photo"],
        }
    },
    responses={
        201: OpenApiResponse(
            response=PhotoSerializer,
            description="Photo uploaded successfully",
            examples=[
                OpenApiExample(
                    "Success",
                    value={
                        "id": 1,
                        "cloudinary_url": "https://res.cloudinary.com/.../dog.jpg",
                        "thumbnail_url": "https://res.cloudinary.com/.../w_300,h_300/dog.jpg",
                        "order_index": 0,
                        "uploaded_at": "2024-12-20T10:30:00Z",
                    },
                )
            ],
        ),
        400: OpenApiResponse(
            description="Validation error",
            examples=[
                OpenApiExample(
                    "Max photos reached",
                    value={
                        "error": "A listing can have a maximum of 2 photos."
                    },
                ),
                OpenApiExample(
                    "File too large",
                    value={
                        "photo": ["File size too large. Maximum size is 5MB."]
                    },
                ),
                OpenApiExample(
                    "Invalid file type",
                    value={
                        "photo": [
                            "Invalid file type. Allowed types: JPEG, PNG, WebP."
                        ]
                    },
                ),
            ],
        ),
        403: OpenApiResponse(
            description="Not the owner of this listing",
            examples=[
                OpenApiExample(
                    "Forbidden",
                    value={
                        "detail": "You do not have permission to perform this action."
                    },
                )
            ],
        ),
        404: OpenApiResponse(description="Listing not found"),
    },
)

delete_photo_schema = extend_schema(
    summary="Delete photo from listing",
    description=(
        "Delete a specific photo from this listing. "
        "Only the listing owner can delete photos. "
        "The photo will also be removed from Cloudinary."
    ),
    responses={
        200: OpenApiResponse(
            response=PhotoDeleteSerializer,
            description="Photo deleted successfully",
            examples=[
                OpenApiExample(
                    "Success",
                    value={
                        "id": 5,
                        "message": "Photo deleted successfully",
                        "deleted_at": "2025-12-20T22:30:00Z",
                    },
                )
            ],
        ),
        403: OpenApiResponse(
            description="Not the owner of this listing",
            examples=[
                OpenApiExample(
                    "Forbidden",
                    value={
                        "detail": "You do not have permission to perform this action."
                    },
                )
            ],
        ),
        404: OpenApiResponse(
            description="Photo not found in this listing",
            examples=[
                OpenApiExample(
                    "Not Found",
                    value={"error": "Photo not found in this listing"},
                )
            ],
        ),
        500: OpenApiResponse(
            description="Server error - failed to delete photo from Cloudinary",
            examples=[
                OpenApiExample(
                    "Server Error",
                    value={
                        "error": "Failed to delete photo: Connection timeout"
                    },
                )
            ],
        ),
    },
)

add_location_schema = extend_schema(
    summary="Add new location to listing",
    description=(
        "Add a new location update to an existing listing. "
        "Any authenticated user can add a location if they spot the dog again."
    ),
    request=LocationSerializer,
    responses={
        201: LocationSerializer,
        400: OpenApiResponse(description="Validation error"),
        401: OpenApiResponse(description="Authentication required"),
        404: OpenApiResponse(description="Listing not found"),
    },
)

delete_location_schema = extend_schema(
    summary="Delete location from listing",
    description=(
        "Delete a specific location from this listing. "
        "Only the listing owner or the user who added the location can delete it."
    ),
    responses={
        200: OpenApiResponse(
            description="Location deleted successfully",
            examples=[
                OpenApiExample(
                    "Success",
                    value={
                        "id": 3,
                        "message": "Location deleted successfully",
                        "deleted_at": "2025-12-20T22:30:00Z",
                    },
                )
            ],
        ),
        403: OpenApiResponse(
            description="Not the owner of this listing or location",
            examples=[
                OpenApiExample(
                    "Forbidden",
                    value={
                        "detail": "You do not have permission to perform this action."
                    },
                )
            ],
        ),
        404: OpenApiResponse(
            description="Location not found in this listing",
            examples=[
                OpenApiExample(
                    "Not Found",
                    value={"error": "Location not found in this listing"},
                )
            ],
        ),
    },
)

check_similar_schema = extend_schema(
    summary="Check for similar listings",
    description=(
        "Search for similar dog listings based on characteristics and location.\n\n"
        "**Use cases:**\n"
        "- search_type='found': Find duplicate 'found' reports (before creating new listing)\n"
        "- search_type='lost': Find potential owners (after creating 'found' listing)"
    ),
    request=SimilarListingSerializer,
    responses={
        200: ListingSerializer(many=True),
        400: OpenApiResponse(description="Validation error"),
    },
)
