import json

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth.models import AnonymousUser

from notifications.notify import notify_user

from .models import (
    Conversation, ConversationMembership, Message, MessageReadStatus
)


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
        await self.channel_layer.group_add(
            self.room_group_name, self.channel_name
        )
        await self.accept()

        sender_ids = await self.mark_all_messages_read()
        if sender_ids:
            await self.channel_layer.group_send(self.room_group_name, {
                'type': 'all_messages_read',
                'user_id': self.user.pk,
                'username': self.user.username,
            })
            for sender_id in sender_ids:
                await notify_user(sender_id, 'all_messages_read', {
                    'conversation_id': self.conversation.pk,
                    'read_by_user_id': self.user.pk,
                })

    async def disconnect(self, _close_code):
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(
                self.room_group_name, self.channel_name
            )

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            await self.send(
                json.dumps({'type': 'error', 'code': 'invalid_json'})
            )
            return
        msg_type = data.get('type')

        if msg_type == 'chat_message':
            if self.conversation.is_closed:
                await self.send(json.dumps(
                    {'type': 'error', 'code': 'conversation_closed'}
                ))
                return
            body = data.get('body', '').strip()
            if not body or len(body) > 10_000:
                await self.send(
                    json.dumps({'type': 'error', 'code': 'invalid_message'})
                )
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

            members = await self.get_conversation_members(self.conversation.pk)
            for member in members:
                if member.user_id != self.user.pk:
                    await notify_user(
                        user_id=member.user_id,
                        event_type="new_message",
                        payload={
                            "conversation_id": self.conversation.pk,
                            "last_message": {
                                "id": message.pk,
                                "body": message.body,
                                "sender_id": message.sender_id,
                                "created_at": message.created_at.isoformat()
                            },
                        }
                    )

        elif msg_type == 'mark_read':
            message_id = data.get('message_id')
            if not isinstance(message_id, int) or message_id <= 0:
                await self.send(
                    json.dumps({'type': 'error', 'code': 'invalid_message'})
                )
                return
            message = await self.mark_message_read(message_id)
            if not message:
                await self.send(
                    json.dumps({'type': 'error', 'code': 'invalid_message'})
                )
                return
            await self.channel_layer.group_send(self.room_group_name, {
                'type': 'message_read',
                'message_id': message_id,
                'user_id': self.user.pk,
                'username': self.user.username,
            })
            if message.sender_id != self.user.pk:
                await notify_user(message.sender_id, 'message_read', {
                    'conversation_id': self.conversation.pk,
                    'message_id': message_id,
                    'read_by_user_id': self.user.pk,
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

    async def all_messages_read(self, event):
        await self.send(text_data=json.dumps({
            'type': 'all_messages_read',
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
            message = Message.objects.get(
                pk=message_id, conversation=self.conversation
            )
        except Message.DoesNotExist:
            return None
        MessageReadStatus.objects.get_or_create(
            message=message, user=self.user
        )
        return message

    @database_sync_to_async
    def get_conversation_members(self, conversation_id):
        return list(ConversationMembership.objects.filter(
            conversation_id=conversation_id
        ))

    @database_sync_to_async
    def mark_all_messages_read(self):
        already_read_ids = MessageReadStatus.objects.filter(
            user_id=self.user.pk,
            message__conversation_id=self.conversation.pk,
        ).values_list('message_id', flat=True)

        unread = list(
            Message.objects.filter(
                conversation_id=self.conversation.pk,
            ).exclude(
                sender_id=self.user.pk,
            ).exclude(
                id__in=already_read_ids,
            )
        )
        if not unread:
            return set()
        MessageReadStatus.objects.bulk_create(
            [
                MessageReadStatus(message_id=msg.pk, user_id=self.user.pk)
                for msg in unread
            ],
            ignore_conflicts=True,
        )
        return {msg.sender_id for msg in unread}
