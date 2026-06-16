from asgiref.sync import async_to_sync

from . import presence
from .models import Notification
from .notify import notify_user
from .serializers import NotificationSerializer
from .tasks import send_push_to_user


def dispatch_notification(user_id, event_type, title, body, data=None):
    """
    Single entry point for non-chat notifications.
    Always persists a Notification. Delivers it live over WebSocket
    when the user is online, otherwise enqueues a push.
    """
    data = data or {}

    notification = Notification.objects.create(
        user_id=user_id,
        event_type=event_type,
        title=title,
        body=body,
        data=data,
    )

    if presence.is_online(user_id):
        async_to_sync(notify_user)(
            user_id=user_id,
            event_type=event_type,
            payload=NotificationSerializer(notification).data,
        )
    else:
        send_push_to_user.delay(
            user_id=user_id,
            event_type=event_type,
            title=title,
            body=body,
            data=data,
        )

    return notification
