import json

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth.models import AnonymousUser

from .models import Conversation, Message, MessageReadStatus


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        user = self.scope.get('user')
        if not user or isinstance(user, AnonymousUser):
            await self.close()
            return

        conversation_id = self.scope['url_route']['kwargs']['conversation_id']
        conversation = await self.get_conversation_or_none(conversation_id)
        if not conversation:
            await self.close()
            return
        if not await self.user_is_member(user, conversation):
            await self.close()
            return

        self.conversation = conversation
        self.user = user
        self.room_group_name = f'chat_{conversation_id}'
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            await self.send(json.dumps({'type': 'error', 'code': 'invalid_json'}))
            return
        msg_type = data.get('type')

        if msg_type == 'chat_message':
            if self.conversation.is_closed:
                await self.send(json.dumps({'type': 'error', 'code': 'conversation_closed'}))
                return
            body = data.get('body', '').strip()
            if not body or len(body) > 10_000:
                await self.send(json.dumps({'type': 'error', 'code': 'invalid_message'}))
                return
            message = await self.save_message(body)
            await self.channel_layer.group_send(self.room_group_name, {
                'type': 'chat_message',
                'message_id': message.pk,
                'body': message.body,
                'sender_id': self.user.pk,
                'sender_username': self.user.username,
                'created_at': message.created_at.isoformat(),
            })

        elif msg_type == 'mark_read':
            message_id = data.get('message_id')
            if not isinstance(message_id, int) or message_id <= 0:
                await self.send(json.dumps({'type': 'error', 'code': 'invalid_message'}))
                return
            if not await self.mark_message_read(message_id):
                await self.send(json.dumps({'type': 'error', 'code': 'invalid_message'}))
                return
            await self.channel_layer.group_send(self.room_group_name, {
                'type': 'message_read',
                'message_id': message_id,
                'user_id': self.user.pk,
                'username': self.user.username,
            })

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'type': 'chat_message',
            'message_id': event['message_id'],
            'body': event['body'],
            'sender_id': event['sender_id'],
            'sender_username': event['sender_username'],
            'created_at': event['created_at'],
        }))

    async def message_read(self, event):
        await self.send(text_data=json.dumps({
            'type': 'message_read',
            'message_id': event['message_id'],
            'user_id': event['user_id'],
            'username': event['username'],
        }))

    @database_sync_to_async
    def get_conversation_or_none(self, conversation_id):
        try:
            return Conversation.objects.get(pk=conversation_id)
        except Conversation.DoesNotExist:
            return None

    @database_sync_to_async
    def user_is_member(self, user, conversation):
        return conversation.memberships.filter(user=user).exists()

    @database_sync_to_async
    def save_message(self, body):
        return Message.objects.create(
            conversation=self.conversation,
            sender=self.user,
            body=body,
        )

    @database_sync_to_async
    def mark_message_read(self, message_id):
        try:
            message = Message.objects.get(pk=message_id, conversation=self.conversation)
        except Message.DoesNotExist:
            return False
        MessageReadStatus.objects.get_or_create(message=message, user=self.user)
        return True
