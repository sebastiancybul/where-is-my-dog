import json

from asgiref.sync import sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth.models import AnonymousUser

from . import presence


class UserNotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        user = self.scope.get("user")
        if not user or isinstance(user, AnonymousUser):
            await self.close()
            return

        self.user = user
        self.room_group_name = f"user_{user.id}"
        await self.channel_layer.group_add(
            self.room_group_name, self.channel_name
        )
        await self.accept()
        await sync_to_async(presence.mark_online)(user.id, self.channel_name)

    async def disconnect(self, code):
        if hasattr(self, "room_group_name"):
            await self.channel_layer.group_discard(
                self.room_group_name, self.channel_name
            )
        if hasattr(self, "user"):
            await sync_to_async(presence.mark_offline)(
                self.user.id, self.channel_name
            )

    async def receive(self, text_data=None, _bytes_data=None):
        if not hasattr(self, "user"):
            return
        try:
            data = json.loads(text_data)
        except (TypeError, json.JSONDecodeError):
            return
        if data.get("type") == "ping":
            await sync_to_async(presence.mark_online)(
                self.user.id, self.channel_name
            )

    async def new_notification(self, event):
        await self.send(
            text_data=json.dumps(
                {
                    "type": "new_notification",
                    "event_type": event["event_type"],
                    "payload": event["payload"],
                }
            )
        )
