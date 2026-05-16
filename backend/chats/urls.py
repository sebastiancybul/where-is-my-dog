from rest_framework.routers import DefaultRouter

from chats.views import ConversationViewSet

router = DefaultRouter()
router.register('conversations', ConversationViewSet, basename='conversation')

urlpatterns = router.urls
