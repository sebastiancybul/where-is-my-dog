import cloudinary.uploader
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from chats.models import Conversation, ConversationMembership, Message, MessagePhoto
from chats.permissions import IsConversationMember, IsListingOwner
from chats.serializers import ConversationSerializer, MessageSerializer
from chats.schemas import (
    archive_schema,
    close_schema,
    conversation_viewset_schema,
    join_schema,
    messages_schema,
    upload_image_schema,
    ws_ticket_schema,
)
from chats.tickets import generate_ticket

User = get_user_model()


@conversation_viewset_schema
class ConversationViewSet(viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = ConversationSerializer

    def get_queryset(self):
        return Conversation.objects.filter(
            memberships__user=self.request.user,
            memberships__is_archived=False,
        )

    def get_permissions(self):
        member_actions = ['retrieve', 'archive', 'messages', 'upload_image']
        if self.action in member_actions:
            return [IsAuthenticated(), IsConversationMember()]
        if self.action == 'close':
            return [IsAuthenticated(), IsListingOwner()]
        return [IsAuthenticated()]

    def list(self, request):
        qs = self.get_queryset().order_by('-messages__created_at').distinct()
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        conversation = get_object_or_404(self.get_queryset(), pk=pk)
        self.check_object_permissions(request, conversation)
        return Response(self.get_serializer(conversation).data)

    def create(self, request):
        other_user_id = request.data.get('user_id')
        if not other_user_id:
            return Response({'user_id': 'This field is required.'}, status=status.HTTP_400_BAD_REQUEST)

        other_user = get_object_or_404(User, pk=other_user_id)
        if other_user == request.user:
            return Response({'user_id': 'Cannot start a conversation with yourself.'}, status=status.HTTP_400_BAD_REQUEST)

        existing = Conversation.objects.filter(
            type=Conversation.TYPE_PRIVATE,
            memberships__user=request.user,
        ).filter(
            memberships__user=other_user,
        ).first()

        if existing:
            return Response(self.get_serializer(existing).data, status=status.HTTP_200_OK)

        conversation = Conversation.objects.create(type=Conversation.TYPE_PRIVATE)
        ConversationMembership.objects.create(user=request.user, conversation=conversation)
        ConversationMembership.objects.create(user=other_user, conversation=conversation)

        return Response(self.get_serializer(conversation).data, status=status.HTTP_201_CREATED)

    @join_schema
    @action(detail=True, methods=['post'])
    def join(self, request, pk=None):
        conversation = get_object_or_404(Conversation, pk=pk, type=Conversation.TYPE_PUBLIC)
        if conversation.is_closed:
            return Response({'detail': 'Conversation is closed.'}, status=status.HTTP_403_FORBIDDEN)
        ConversationMembership.objects.get_or_create(user=request.user, conversation=conversation)
        return Response(self.get_serializer(conversation).data)

    @close_schema
    @action(detail=True, methods=['post'])
    def close(self, request, pk=None):
        conversation = get_object_or_404(Conversation, pk=pk)
        self.check_object_permissions(request, conversation)
        conversation.is_closed = True
        conversation.save(update_fields=['is_closed'])
        return Response(status=status.HTTP_204_NO_CONTENT)

    @archive_schema
    @action(detail=True, methods=['post'])
    def archive(self, request, pk=None):
        conversation = get_object_or_404(self.get_queryset(), pk=pk)
        self.check_object_permissions(request, conversation)
        ConversationMembership.objects.filter(
            user=request.user,
            conversation=conversation,
        ).update(is_archived=True)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @messages_schema
    @action(detail=True, methods=['get'])
    def messages(self, request, pk=None):
        conversation = get_object_or_404(self.get_queryset(), pk=pk)
        self.check_object_permissions(request, conversation)
        qs = conversation.messages.order_by('-created_at').prefetch_related('photos')
        page = self.paginate_queryset(qs)
        if page is not None:
            return self.get_paginated_response(MessageSerializer(page, many=True).data)
        return Response(MessageSerializer(qs, many=True).data)

    @upload_image_schema
    @action(detail=True, methods=['post'], url_path='upload_image')
    def upload_image(self, request, pk=None):
        conversation = get_object_or_404(self.get_queryset(), pk=pk)
        self.check_object_permissions(request, conversation)

        if conversation.is_closed:
            return Response({'detail': 'Conversation is closed.'}, status=status.HTTP_403_FORBIDDEN)

        image = request.FILES.get('image')
        if not image:
            return Response({'image': 'This field is required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            result = cloudinary.uploader.upload(image, folder='chats/photos', resource_type='image')
        except Exception:
            return Response({'detail': 'Upload failed.'}, status=status.HTTP_502_BAD_GATEWAY)

        message = Message.objects.create(conversation=conversation, sender=request.user, body='')
        photo = MessagePhoto.objects.create(
            message=message,
            image=result['secure_url'],
            cloudinary_public_id=result['public_id'],
        )

        async_to_sync(get_channel_layer().group_send)(
            f'chat_{conversation.pk}',
            {
                'type': 'chat_message',
                'message_id': message.pk,
                'body': '',
                'sender_id': request.user.pk,
                'sender_username': request.user.username,
                'created_at': message.created_at.isoformat(),
            },
        )

        return Response(MessageSerializer(message).data, status=status.HTTP_201_CREATED)


@ws_ticket_schema
class WsTicketView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        ticket = generate_ticket(request.user.pk)
        return Response({"ticket": ticket})
