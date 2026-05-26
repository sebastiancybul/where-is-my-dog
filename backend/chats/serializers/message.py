from rest_framework import serializers

from chats.models import Message, MessagePhoto


class MessagePhotoSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()

    class Meta:
        model = MessagePhoto
        fields = ['id', 'url', 'uploaded_at']

    def get_url(self, obj):
        return obj.image.url


class MessageSerializer(serializers.ModelSerializer):
    photos = MessagePhotoSerializer(many=True, read_only=True)
    sender_username = serializers.CharField(source='sender.username', read_only=True)
    read_by = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = ['id', 'body', 'photos', 'sender_id', 'sender_username', 'created_at', 'read_by']

    def get_read_by(self, obj):
        return list(obj.read_statuses.values_list('user_id', flat=True))
