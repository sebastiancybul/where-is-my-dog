"""
ASGI config for config project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.0/howto/deployment/asgi/
"""

import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django_asgi_app = get_asgi_application()

from chats.middleware import WsTicketMiddleware
from chats.routing import websocket_urlpatterns as chat_urlpatterns
from notifications.routing import websocket_urlpatterns as notification_urlpatterns

application = ProtocolTypeRouter({
    'http': django_asgi_app,
    'websocket': WsTicketMiddleware(URLRouter(chat_urlpatterns + notification_urlpatterns)),
})
