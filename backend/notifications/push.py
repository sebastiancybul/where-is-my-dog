import logging

import firebase_admin
from django.conf import settings
from firebase_admin import credentials, exceptions, messaging

from .models import DeviceToken

logger = logging.getLogger(__name__)


def _ensure_app():
    """Initialize the firebase-admin app once."""
    if not firebase_admin._apps:
        cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS_FILE)
        firebase_admin.initialize_app(cred)


def send_to_user(user_id, event_type, title, body, data=None):
    """
    Send a push notification to all of a user's registered devices.
    Prunes tokens that FCM reports as dead.
    Returns the number of successful deliveries.
    """
    tokens = list(
        DeviceToken.objects.filter(user_id=user_id).values_list(
            "token", flat=True
        )
    )
    if not tokens:
        return 0

    _ensure_app()

    payload = {"event_type": event_type, **(data or {})}
    payload = {key: str(val) for key, val in payload.items()}

    message = messaging.MulticastMessage(
        notification=messaging.Notification(title=title, body=body),
        data=payload,
        tokens=tokens,
    )

    response = messaging.send_each_for_multicast(message)

    dead_tokens = []
    for token, resp in zip(tokens, response.responses):
        if resp.success:
            continue
        exc = resp.exception
        if isinstance(
            exc,
            (
                messaging.UnregisteredError,
                messaging.SenderIdMismatchError,
                exceptions.InvalidArgumentError,
            ),
        ):
            dead_tokens.append(token)
        else:
            logger.warning(
                "Push to user %s failed for a token: %s", user_id, exc
            )

    if dead_tokens:
        DeviceToken.objects.filter(token__in=dead_tokens).delete()

    return response.success_count
