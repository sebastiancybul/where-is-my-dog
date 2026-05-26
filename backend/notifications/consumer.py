import json

from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth.models import AnonymousUser


class UserNotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        user = self.scope.get('user')
        if not user or isinstance(user, AnonymousUser):
            await self.close()
            return

        self.user = user
        self.room_group_name = f'user_{user.id}'
        await self.channel_layer.group_add(
            self.room_group_name, self.channel_name
        )
        await self.accept()

    async def disconnect(self, code):
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )

    async def receive(self, _text_data=None, _bytes_data=None):
        pass

    async def new_notification(self, event):
        await self.send(text_data=json.dumps({
            'type': 'new_notification',
            'event_type': event['event_type'],
            'payload': event['payload']
        }))
