from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for User model (read-only for now)
    """

    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'email',
            'phone',
            'profile_photo',
            'email_verified',
            'is_moderator',
            'is_banned',
            'created_at',
        )
        read_only_fields = (
            'id',
            'email_verified',
            'is_moderator',
            'is_banned',
            'created_at',
        )


class RegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration
    """

    password2 = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )

    class Meta:
        model = User
        fields = (
            'username',
            'email',
            'password',
            'password2',
            'phone',
        )
        extra_kwargs = {
            'password': {
                'write_only': True,
                'style': {'input_type': 'password'}
            }
        }

    def validate(self, attrs):
        """
        Validate that passwords match
        """

        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({
                "password": "Passwords do not match"
            })

        return attrs

    def create(self, validated_data):
        """
        Create user iwth hashed password
        """
        validated_data.pop('password2')

        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            phone=validated_data.get('phone', '')
        )

        return user


class UserPublicSerializer(serializers.ModelSerializer):
    """
    Public user representation safe for use in nested serializers.
    Excludes sensitive fields (email, phone).
    """
    profile_photo = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'profile_photo'
        )
        read_only_fields = fields

    def get_profile_photo(self, obj):
        if obj.profile_photo:
            return obj.profile_photo
        return None


class UpdateProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(required=False)
    phone = serializers.CharField(required=False)

    class Meta:
        model = User
        fields = (
            'username',
            'phone'
        )

    def validate_username(self, value):
        if User.objects.filter(username=value).exclude(pk=self.instance.pk).exists():
            raise serializers.ValidationError("A user with that username already exists.")
        return value

    def validate_phone(self, value):
        if User.objects.filter(phone=value).exclude(pk=self.instance.pk).exists():
            raise serializers.ValidationError("This phone number is already in use.")
        return value


class ChangePasswordSerializer(serializers.Serializer):
    password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)
    new_password2 = serializers.CharField(write_only=True)

    def validate(self, data):
        if data['new_password'] != data['new_password2']:
            raise serializers.ValidationError({"new_password2": "Passwords do not match"})
        
        user = self.context['request'].user
        if not user.check_password(data['password']):
            raise serializers.ValidationError({"password": "Password is incorrect."})

        return data
    


class DeleteAccountSerializer(serializers.Serializer):
    password = serializers.CharField(write_only=True)
    
    def validate(self, data):
        user = self.context['request'].user
        if not user.check_password(data['password']):
            raise serializers.ValidationError({"password": "Password is incorrect."})
        return data


