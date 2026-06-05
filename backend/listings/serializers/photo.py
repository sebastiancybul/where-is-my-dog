from rest_framework import serializers
from ..models import Photo

import cloudinary.uploader
from cloudinary import CloudinaryImage


class PhotoSerializer(serializers.ModelSerializer):
    """
    Serializer for Photo model.
    Used for displaying photos attached to listings.
    """

    cloudinary_url = serializers.SerializerMethodField()

    def get_cloudinary_url(self, obj):
        if obj.cloudinary_url:
            return str(obj.cloudinary_url)
        return None

    class Meta:
        model = Photo
        fields = (
            "id",
            "cloudinary_url",
            "thumbnail_url",
            "order_index",
            "uploaded_at",
        )
        read_only_fields = (
            "id",
            "thumbnail_url",
            "uploaded_at",
        )


class PhotoUploadSerializer(serializers.ModelSerializer):
    """
    Serializer for uploading photos to listings.
    Handles Cloudinary upload and thumbnail generation.
    """

    photo = serializers.ImageField(write_only=True)

    class Meta:
        model = Photo
        fields = [
            "id",
            "listing",
            "photo",
            "cloudinary_url",
            "cloudinary_public_id",
            "thumbnail_url",
            "order_index",
            "file_size",
            "width",
            "height",
            "uploaded_at",
        ]
        read_only_fields = [
            "id",
            "cloudinary_url",
            "cloudinary_public_id",
            "thumbnail_url",
            "file_size",
            "width",
            "height",
            "uploaded_at",
        ]

    def validate_photo(self, value):
        """
        Validate uploaded photo:
        - File size (max 5MB)
        - File type (only JPEG, PNG, WebP)
        """

        max_size = 5 * 1024 * 1024
        if value.size > max_size:
            raise serializers.ValidationError(
                f"File size too large. Maximum size is 5MB. "
                f"Your file is {value.size / (1024 * 1024):.2f}MB"
            )

        allowed_types = ["image/jpeg", "image/png", "image/webp"]
        if value.content_type not in allowed_types:
            raise serializers.ValidationError(
                f"Invalid file type. Allowed types: JPEG, PNG, WebP. "
                f"You uploaded: {value.content_type}"
            )

        return value

    def validate(self, attrs):
        """
        Validate that listing doesn't exceed photo limit.
        """
        listing = attrs.get("listing")

        if listing and listing.photos.count() >= 2:
            raise serializers.ValidationError(
                "A listing can have a maximum of two photos."
            )
        return attrs

    def create(self, validated_data):
        """
        Upload photo to Cloudinary and create Photo instance.
        """
        image = validated_data.pop("photo")

        try:
            upload_result = cloudinary.uploader.upload(
                image,
                folder="listings/photos",
                resource_type="image",
            )
        except Exception as e:
            raise serializers.ValidationError(
                f"Failed to upload photo to Cloudinary: {str(e)}"
            )

        validated_data["cloudinary_url"] = upload_result.get("secure_url")
        validated_data["cloudinary_public_id"] = upload_result.get("public_id")
        validated_data["file_size"] = upload_result.get("bytes")
        validated_data["width"] = upload_result.get("width")
        validated_data["height"] = upload_result.get("height")

        thumbnail_url = CloudinaryImage(upload_result["public_id"]).build_url(
            width=300,
            height=300,
            crop="fill",
            quality="auto",
            fetch_format="auto",
        )
        validated_data["thumbnail_url"] = thumbnail_url

        photo = Photo.objects.create(**validated_data)
        return photo


class PhotoDeleteSerializer(serializers.Serializer):
    """
    Serializer for photo deletion response.
    Returns confirmation of deletion.
    """

    id = serializers.IntegerField(read_only=True)
    message = serializers.CharField(read_only=True)
    deleted_at = serializers.DateTimeField(read_only=True)
