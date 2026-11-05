from django.core.exceptions import ValidationError
from PIL import Image

MAX_IMAGE_SIZE = 5 * 1024 * 1024
ALLOWED_IMAGE_FORMATS = {"JPEG", "PNG", "WEBP"}


def validate_image(file):
    if file.size > MAX_IMAGE_SIZE:
        raise ValidationError(
            f"File size too large. Maximum size is 5MB. "
            f"Your file is {file.size / (1024 * 1024):.2f}MB"
        )

    try:
        with Image.open(file) as image:
            image_format = image.format
            image.verify()
    except (OSError, SyntaxError, ValueError, Image.DecompressionBombError):
        raise ValidationError("Upload a valid image.")
    finally:
        file.seek(0)

    if image_format not in ALLOWED_IMAGE_FORMATS:
        raise ValidationError(
            "Invalid file type. Allowed types: JPEG, PNG, WebP."
        )
