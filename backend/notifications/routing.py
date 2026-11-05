from django.urls import path

from .consumer import UserNotificationConsumer

websocket_urlpatterns = [
    path("ws/v1/notifications/", UserNotificationConsumer.as_asgi()),
]
