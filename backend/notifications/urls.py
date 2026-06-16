from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import DeviceTokenView, NotificationViewSet

app_name = "notifications"

router = DefaultRouter()
router.register("", NotificationViewSet, basename="notification")

urlpatterns = [
    path("devices/", DeviceTokenView.as_view(), name="device-token"),
] + router.urls
