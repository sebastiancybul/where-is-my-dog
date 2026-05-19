from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiResponse,
    extend_schema,
    extend_schema_view,
)

from chats.serializers import ConversationSerializer, MessageSerializer

conversation_viewset_schema = extend_schema_view(
    list=extend_schema(
        tags=['Chats'],
        summary='List my conversations',
        description='Returns all non-archived conversations for the current user, ordered by most recent message.',
        responses={200: ConversationSerializer(many=True)},
    ),
    retrieve=extend_schema(
        tags=['Chats'],
        summary='Get conversation details',
        responses={
            200: ConversationSerializer,
            403: OpenApiResponse(description='Not a member of this conversation'),
            404: OpenApiResponse(description='Conversation not found'),
        },
    ),
    create=extend_schema(
        tags=['Chats'],
        summary='Create private 1:1 conversation',
        description='Creates a new private conversation with another user. Returns existing conversation if one already exists.',
        request={'application/json': {'type': 'object', 'properties': {'user_id': {'type': 'integer'}}, 'required': ['user_id']}},
        responses={
            200: ConversationSerializer,
            201: ConversationSerializer,
            400: OpenApiResponse(description='Missing or invalid user_id'),
        },
    ),
)

join_schema = extend_schema(
    tags=['Chats'],
    summary='Join a public conversation',
    description='Adds the current user as a member of a public conversation.',
    request=None,
    responses={
        200: ConversationSerializer,
        403: OpenApiResponse(description='Conversation is closed'),
        404: OpenApiResponse(description='Conversation not found or not public'),
    },
)

close_schema = extend_schema(
    tags=['Chats'],
    summary='Close a conversation',
    description='Closes the conversation. Only the listing owner can perform this action.',
    request=None,
    responses={
        204: OpenApiResponse(description='Conversation closed'),
        403: OpenApiResponse(description='Not the listing owner'),
    },
)

archive_schema = extend_schema(
    tags=['Chats'],
    summary='Archive conversation for current user',
    description='Hides the conversation from the current user\'s list. Other members are not affected.',
    request=None,
    responses={
        204: OpenApiResponse(description='Conversation archived'),
        403: OpenApiResponse(description='Not a member of this conversation'),
    },
)

messages_schema = extend_schema(
    tags=['Chats'],
    summary='Get message history',
    description='Returns paginated messages for a conversation, newest first.',
    responses={
        200: MessageSerializer(many=True),
        403: OpenApiResponse(description='Not a member of this conversation'),
    },
)

ws_ticket_schema = extend_schema(
    tags=['Chats'],
    summary='Generate WebSocket ticket',
    description='Issues a single-use, 30-second ticket for authenticating a WebSocket connection. Pass the ticket as ?ticket=... in the WebSocket URL.',
    request=None,
    responses={
        200: OpenApiResponse(
            description='Ticket generated',
            examples=[OpenApiExample('Ticket', value={'ticket': 'abc123...'})],
        ),
    },
)

upload_image_schema = extend_schema(
    tags=['Chats'],
    summary='Send image message',
    description='Uploads an image to Cloudinary, creates a message, and broadcasts it to all connected WebSocket clients.',
    request={'multipart/form-data': {'type': 'object', 'properties': {'image': {'type': 'string', 'format': 'binary'}}, 'required': ['image']}},
    responses={
        201: MessageSerializer,
        400: OpenApiResponse(description='No image provided'),
        403: OpenApiResponse(description='Conversation is closed or not a member'),
        502: OpenApiResponse(
            description='Cloudinary upload failed',
            examples=[OpenApiExample('Upload error', value={'detail': 'Upload failed.'})],
        ),
    },
)
