from django.urls import path

from .consumer import UserNotificationConsumer

websocket_urlpatterns = [
    path('ws/notifications/', UserNotificationConsumer.as_asgi()),
]
