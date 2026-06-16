from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import (
    OpenApiParameter,
    OpenApiResponse,
    extend_schema,
    extend_schema_view,
)

from .serializers import DeviceTokenSerializer, NotificationSerializer

device_token_schema = extend_schema_view(
    post=extend_schema(
        tags=["Notifications"],
        summary="Register a device token",
        description="Registers or updates the FCM token for the current user's device.",
        request=DeviceTokenSerializer,
        responses={200: DeviceTokenSerializer},
    ),
    delete=extend_schema(
        tags=["Notifications"],
        summary="Unregister a device token",
        description="Removes the given FCM token for the current user.",
        parameters=[
            OpenApiParameter(
                name="token",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                required=True,
                description="FCM token to remove",
            )
        ],
        responses={
            204: OpenApiResponse(description="Token removed"),
            400: OpenApiResponse(description="token is required"),
        },
    ),
)

notification_viewset_schema = extend_schema_view(
    list=extend_schema(
        tags=["Notifications"],
        summary="List my notifications",
        description="Returns the current user's notifications, newest first, paginated.",
        responses={200: NotificationSerializer(many=True)},
    ),
    read=extend_schema(
        tags=["Notifications"],
        summary="Mark one notification as read",
        description="Marks a single notification owned by the current user as read.",
        request=None,
        responses={
            204: OpenApiResponse(description="Notification marked as read"),
            404: OpenApiResponse(
                description="Notification not found or not owned by user"
            ),
        },
    ),
    read_all=extend_schema(
        tags=["Notifications"],
        summary="Mark all notifications as read",
        description="Marks every unread notification of the current user as read.",
        request=None,
        responses={
            204: OpenApiResponse(
                description="All notifications marked as read"
            )
        },
    ),
)
