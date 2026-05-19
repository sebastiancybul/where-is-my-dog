from urllib.parse import parse_qs

from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser

from .tickets import consume_ticket

User = get_user_model()


class WsTicketMiddleware(BaseMiddleware):
    async def __call__(self, scope, receive, send):
        params = parse_qs(scope.get("query_string", b"").decode())
        ticket = params.get("ticket", [None])[0]
        scope["user"] = await self.get_user(ticket)
        return await super().__call__(scope, receive, send)

    @database_sync_to_async
    def get_user(self, ticket):
        if not ticket:
            return AnonymousUser()
        user_id = consume_ticket(ticket)
        if not user_id:
            return AnonymousUser()
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return AnonymousUser()
