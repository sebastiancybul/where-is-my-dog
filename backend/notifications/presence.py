import redis
from django.conf import settings

_client = None

ONLINE_TTL_SECONDS = 90


def _redis():
    global _client
    if _client is None:
        _client = redis.from_url(settings.REDIS_URL, decode_responses=True)
    return _client


def _key(user_id):
    return f"presence:online:{user_id}"


def mark_online(user_id, channel_name):
    key = _key(user_id)
    client = _redis()
    client.sadd(key, channel_name)
    client.expire(key, ONLINE_TTL_SECONDS)


def mark_offline(user_id, channel_name):
    _redis().srem(_key(user_id), channel_name)


def is_online(user_id):
    return _redis().scard(_key(user_id)) > 0
