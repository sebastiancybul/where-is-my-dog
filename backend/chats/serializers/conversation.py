from rest_framework import serializers

from chats.models import Conversation

from .message import MessageSerializer


class ConversationSerializer(serializers.ModelSerializer):
    last_message = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = ['id', 'type', 'listing_id', 'is_closed', 'last_message', 'created_at']

    def get_last_message(self, obj):
        message = obj.messages.last()
        if not message:
            return None
        return MessageSerializer(message).data
