"""
Tests for the shared image upload validator
"""

import io
from unittest.mock import patch

from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from PIL import Image

from listings.validators import MAX_IMAGE_SIZE, validate_image


def image_bytes(image_format, size=(10, 10)):
    """Return the bytes of a small solid-colour image in the given format"""
    buffer = io.BytesIO()
    Image.new("RGB", size, "red").save(buffer, format=image_format)
    return buffer.getvalue()


def uploaded(content, name="photo.jpg", content_type="image/jpeg"):
    return SimpleUploadedFile(name, content, content_type=content_type)


class ValidateImageTests(TestCase):
    """Tests for validate_image"""

    def assert_rejected(self, file, expected_message):
        with self.assertRaises(ValidationError) as ctx:
            validate_image(file)
        self.assertIn(expected_message, ctx.exception.messages[0])

    def test_jpeg_accepted(self):
        validate_image(uploaded(image_bytes("JPEG")))

    def test_png_accepted(self):
        validate_image(
            uploaded(
                image_bytes("PNG"), name="photo.png", content_type="image/png"
            )
        )

    def test_webp_accepted(self):
        validate_image(
            uploaded(
                image_bytes("WEBP"),
                name="photo.webp",
                content_type="image/webp",
            )
        )

    def test_gif_with_jpeg_content_type_rejected(self):
        """The real format comes from the bytes, not the client header"""
        file = uploaded(image_bytes("GIF"))

        self.assert_rejected(
            file, "Invalid file type. Allowed types: JPEG, PNG, WebP."
        )

    def test_text_named_jpg_rejected(self):
        file = uploaded(b"definitely not an image")

        self.assert_rejected(file, "Upload a valid image.")

    def test_truncated_jpeg_rejected(self):
        file = uploaded(image_bytes("JPEG")[:100])

        self.assert_rejected(file, "Upload a valid image.")

    def test_file_over_5mb_rejected(self):
        padding = b"\0" * (MAX_IMAGE_SIZE + 1)
        file = uploaded(image_bytes("JPEG") + padding)

        self.assert_rejected(
            file, "File size too large. Maximum size is 5MB. Your file is"
        )

    def test_file_exactly_5mb_not_rejected_for_size(self):
        content = image_bytes("JPEG")
        content += b"\0" * (MAX_IMAGE_SIZE - len(content))
        file = uploaded(content)

        validate_image(file)

    def test_file_position_reset_after_valid_image(self):
        file = uploaded(image_bytes("JPEG"))

        validate_image(file)

        self.assertEqual(file.tell(), 0)

    def test_file_position_reset_after_invalid_image(self):
        file = uploaded(b"definitely not an image")

        with self.assertRaises(ValidationError):
            validate_image(file)

        self.assertEqual(file.tell(), 0)

    def test_decompression_bomb_rejected(self):
        file = uploaded(image_bytes("PNG", size=(100, 100)))

        with patch("PIL.Image.MAX_IMAGE_PIXELS", 10):
            self.assert_rejected(file, "Upload a valid image.")
