import secrets

import redis
from django.conf import settings

TICKET_TTL = 30
_PREFIX = "ws_ticket:"


def _client():
    return redis.from_url(settings.CELERY_BROKER_URL, decode_responses=True)


def generate_ticket(user_id: int) -> str:
    ticket = secrets.token_urlsafe(32)
    _client().setex(f"{_PREFIX}{ticket}", TICKET_TTL, str(user_id))
    return ticket


def consume_ticket(ticket: str) -> int | None:
    user_id = _client().getdel(f"{_PREFIX}{ticket}")
    return int(user_id) if user_id else None
