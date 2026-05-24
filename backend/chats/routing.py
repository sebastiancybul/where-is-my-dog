from django.urls import path, re_path

from .notification_consumer import UserNotificationConsumer

from .consumers import ChatConsumer

websocket_urlpatterns = [
    re_path(r'^ws/chats/(?P<conversation_id>\d+)/$', ChatConsumer.as_asgi()),
    path("ws/notifications/", UserNotificationConsumer.as_asgi())
]
