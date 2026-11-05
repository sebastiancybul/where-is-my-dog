import io
from unittest.mock import AsyncMock, patch

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from PIL import Image
from rest_framework import status
from rest_framework.test import APITestCase

from chats.models import (
    Conversation,
    ConversationMembership,
    Message,
    MessagePhoto,
)

User = get_user_model()

FAKE_UPLOAD = {
    "secure_url": "https://cdn.example.com/chats/photos/p.jpg",
    "public_id": "chats/photos/p",
}


def create_user(**params):
    defaults = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpass123",
    }
    defaults.update(params)
    return User.objects.create_user(**defaults)


def image_file():
    buffer = io.BytesIO()
    Image.new("RGB", (10, 10), "red").save(buffer, format="JPEG")
    return SimpleUploadedFile(
        "photo.jpg", buffer.getvalue(), content_type="image/jpeg"
    )


class UploadImageApiTests(APITestCase):
    def setUp(self):
        self.user = create_user(username="u1", email="u1@example.com")
        self.other = create_user(username="u2", email="u2@example.com")
        self.conversation = Conversation.objects.create(
            type=Conversation.TYPE_PRIVATE
        )
        ConversationMembership.objects.create(
            user=self.user, conversation=self.conversation
        )
        ConversationMembership.objects.create(
            user=self.other, conversation=self.conversation
        )
        self.url = reverse(
            "conversation-upload-image", args=[self.conversation.pk]
        )

    def test_unauthenticated_returns_401(self):
        res = self.client.post(
            self.url, {"image": image_file()}, format="multipart"
        )
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    @patch("chats.views.conversation.notify_user", new_callable=AsyncMock)
    @patch("chats.views.conversation.get_channel_layer")
    @patch("cloudinary.uploader.upload", return_value=FAKE_UPLOAD)
    def test_upload_creates_message_and_photo(
        self, _mock_upload, mock_layer, _mock_notify
    ):
        mock_layer.return_value.group_send = AsyncMock()
        self.client.force_authenticate(user=self.user)

        res = self.client.post(
            self.url, {"image": image_file()}, format="multipart"
        )

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Message.objects.count(), 1)
        self.assertEqual(MessagePhoto.objects.count(), 1)
        photo = MessagePhoto.objects.get()
        self.assertEqual(photo.cloudinary_public_id, FAKE_UPLOAD["public_id"])
        self.assertEqual(len(res.data["photos"]), 1)

    @patch("chats.views.conversation.notify_user", new_callable=AsyncMock)
    @patch("chats.views.conversation.get_channel_layer")
    @patch("cloudinary.uploader.upload", return_value=FAKE_UPLOAD)
    def test_broadcast_includes_photos(
        self, _mock_upload, mock_layer, _mock_notify
    ):
        mock_group_send = AsyncMock()
        mock_layer.return_value.group_send = mock_group_send
        self.client.force_authenticate(user=self.user)

        self.client.post(self.url, {"image": image_file()}, format="multipart")

        mock_group_send.assert_called_once()
        group_name, event = mock_group_send.call_args.args
        self.assertEqual(group_name, f"chat_{self.conversation.pk}")
        self.assertEqual(event["type"], "chat_message")
        self.assertEqual(len(event["photos"]), 1)
        self.assertEqual(event["photos"][0]["url"], FAKE_UPLOAD["secure_url"])

    @patch("chats.views.conversation.notify_user", new_callable=AsyncMock)
    @patch("chats.views.conversation.get_channel_layer")
    @patch("cloudinary.uploader.upload", return_value=FAKE_UPLOAD)
    def test_notifies_only_other_member_with_has_photo(
        self, _mock_upload, mock_layer, mock_notify
    ):
        mock_layer.return_value.group_send = AsyncMock()
        self.client.force_authenticate(user=self.user)

        self.client.post(self.url, {"image": image_file()}, format="multipart")

        mock_notify.assert_called_once()
        kwargs = mock_notify.call_args.kwargs
        self.assertEqual(kwargs["user_id"], self.other.id)
        self.assertEqual(kwargs["event_type"], "new_message")
        last_message = kwargs["payload"]["last_message"]
        self.assertTrue(last_message["has_photo"])
        self.assertEqual(last_message["body"], "")

    @patch("chats.views.conversation.notify_user", new_callable=AsyncMock)
    @patch("chats.views.conversation.get_channel_layer")
    @patch("cloudinary.uploader.upload", return_value=FAKE_UPLOAD)
    def test_missing_image_returns_400(
        self, _mock_upload, mock_layer, _mock_notify
    ):
        mock_layer.return_value.group_send = AsyncMock()
        self.client.force_authenticate(user=self.user)

        res = self.client.post(self.url, {}, format="multipart")

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Message.objects.count(), 0)

    @patch("chats.views.conversation.send_push_to_user")
    @patch("chats.views.conversation.notify_user", new_callable=AsyncMock)
    @patch("chats.views.conversation.get_channel_layer")
    @patch("cloudinary.uploader.upload", return_value=FAKE_UPLOAD)
    def test_invalid_image_returns_400_without_upload(
        self, mock_upload, mock_layer, mock_notify, mock_push
    ):
        mock_layer.return_value.group_send = AsyncMock()
        self.client.force_authenticate(user=self.user)
        fake = SimpleUploadedFile(
            "photo.jpg", b"fake-image-bytes", content_type="image/jpeg"
        )

        res = self.client.post(self.url, {"image": fake}, format="multipart")

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("image", res.data)
        mock_upload.assert_not_called()
        self.assertEqual(Message.objects.count(), 0)
        mock_layer.return_value.group_send.assert_not_called()
        mock_notify.assert_not_called()
        mock_push.delay.assert_not_called()

    @patch("chats.views.conversation.notify_user", new_callable=AsyncMock)
    @patch("chats.views.conversation.get_channel_layer")
    @patch("cloudinary.uploader.upload", return_value=FAKE_UPLOAD)
    def test_image_over_5mb_returns_400(
        self, mock_upload, mock_layer, _mock_notify
    ):
        mock_layer.return_value.group_send = AsyncMock()
        self.client.force_authenticate(user=self.user)
        oversized = SimpleUploadedFile(
            "photo.jpg",
            image_file().read() + b"\0" * (5 * 1024 * 1024),
            content_type="image/jpeg",
        )

        res = self.client.post(
            self.url, {"image": oversized}, format="multipart"
        )

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("File size too large", str(res.data["image"][0]))
        mock_upload.assert_not_called()
        self.assertEqual(Message.objects.count(), 0)

    @patch("chats.views.conversation.send_push_to_user")
    @patch("chats.views.conversation.notify_user", new_callable=AsyncMock)
    @patch("chats.views.conversation.get_channel_layer")
    @patch("cloudinary.uploader.destroy")
    @patch("cloudinary.uploader.upload", return_value=FAKE_UPLOAD)
    def test_db_failure_rolls_back_and_destroys_upload(
        self, mock_upload, mock_destroy, mock_layer, mock_notify, mock_push
    ):
        """
        The Message must not survive without its photo, and the Cloudinary
        file must not be orphaned.
        """
        mock_layer.return_value.group_send = AsyncMock()
        self.client.force_authenticate(user=self.user)
        self.client.raise_request_exception = False

        with patch(
            "chats.views.conversation.MessagePhoto.objects.create",
            side_effect=RuntimeError("db down"),
        ):
            res = self.client.post(
                self.url, {"image": image_file()}, format="multipart"
            )

        self.assertEqual(
            res.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR
        )
        mock_upload.assert_called_once()
        mock_destroy.assert_called_once_with(FAKE_UPLOAD["public_id"])
        self.assertEqual(Message.objects.count(), 0)
        self.assertEqual(MessagePhoto.objects.count(), 0)
        mock_layer.return_value.group_send.assert_not_called()
        mock_notify.assert_not_called()
        mock_push.delay.assert_not_called()
