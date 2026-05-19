from django.urls import path
from rest_framework.routers import DefaultRouter

from chats.views import ConversationViewSet, WsTicketView

router = DefaultRouter()
router.register('conversations', ConversationViewSet, basename='conversation')

urlpatterns = router.urls + [
    path('ws-ticket/', WsTicketView.as_view(), name='ws-ticket'),
]