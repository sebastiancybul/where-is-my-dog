from drf_spectacular.utils import (
    extend_schema,
    OpenApiResponse,
    OpenApiExample,
)

from .serializers import (
    UserSerializer,
    RegistrationSerializer,
    UpdateProfileSerializer,
    ChangePasswordSerializer,
    DeleteAccountSerializer,
)

_user_example = {
    "id": 1,
    "username": "john",
    "email": "john@example.com",
    "phone": "123456789",
    "profile_photo": None,
    "email_verified": False,
    "is_moderator": False,
    "is_banned": False,
    "created_at": "2025-12-18T13:00:00Z",
}

_tokens_example = {
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbG...",
    "access": "eyJ0eXAiOiJKV1QiLCJhbG...",
}

register_schema = extend_schema(
    tags=["Authentication"],
    summary="Register new user",
    description="Create a new user account and receive JWT tokens",
    request=RegistrationSerializer,
    responses={
        201: OpenApiResponse(
            response=UserSerializer,
            description="User registered successfully",
            examples=[
                OpenApiExample(
                    "Success",
                    value={"user": _user_example, "tokens": _tokens_example},
                )
            ],
        ),
        400: OpenApiResponse(description="Validation error"),
    },
)

login_schema = extend_schema(
    tags=["Authentication"],
    summary="Login user",
    description="Authenticate user and receive JWT tokens",
    request={
        "application/json": {
            "type": "object",
            "properties": {
                "email": {
                    "type": "string",
                    "example": "john@example.com",
                    "format": "email",
                },
                "password": {
                    "type": "string",
                    "example": "secret123",
                    "format": "password",
                },
            },
            "required": ["email", "password"],
        }
    },
    responses={
        200: OpenApiResponse(
            response=UserSerializer,
            description="Login successful",
            examples=[
                OpenApiExample(
                    "Success",
                    value={"user": _user_example, "tokens": _tokens_example},
                )
            ],
        ),
        401: OpenApiResponse(
            description="Invalid credentials",
            examples=[
                OpenApiExample("Error", value={"error": "Invalid credentials"})
            ],
        ),
    },
)

current_user_schema = extend_schema(
    tags=["Authentication"],
    summary="Get current user",
    description="Retrieve currently authenticated user information",
    responses={
        200: UserSerializer,
        401: OpenApiResponse(
            description="Authentication credentials were not provided"
        ),
    },
)

update_profile_schema = extend_schema(
    tags=["Settings"],
    summary="Update profile",
    description="Update username and/or phone number. All fields are optional.",
    request=UpdateProfileSerializer,
    responses={
        200: UpdateProfileSerializer,
        400: OpenApiResponse(description="Validation error"),
        401: OpenApiResponse(description="Authentication required"),
    },
)

change_password_schema = extend_schema(
    tags=["Settings"],
    summary="Change password",
    request=ChangePasswordSerializer,
    responses={
        200: OpenApiResponse(
            description="Password changed successfully",
            examples=[
                OpenApiExample(
                    "Success",
                    value={"detail": "Password changed successfully."},
                )
            ],
        ),
        400: OpenApiResponse(
            description="Validation error",
            examples=[
                OpenApiExample(
                    "Wrong old password",
                    value={"password": ["Old password is incorrect."]},
                ),
                OpenApiExample(
                    "Passwords mismatch",
                    value={"new_password2": ["Passwords do not match"]},
                ),
            ],
        ),
        401: OpenApiResponse(description="Authentication required"),
    },
)

delete_account_schema = extend_schema(
    tags=["Settings"],
    summary="Delete account",
    description="Permanently delete the authenticated user account. Requires password confirmation.",
    request=DeleteAccountSerializer,
    responses={
        200: OpenApiResponse(
            description="Account deleted successfully",
            examples=[
                OpenApiExample(
                    "Success",
                    value={"detail": "Account deleted successfully."},
                )
            ],
        ),
        400: OpenApiResponse(
            description="Validation error",
            examples=[
                OpenApiExample(
                    "Wrong password",
                    value={"password": ["Password is incorrect."]},
                )
            ],
        ),
        401: OpenApiResponse(description="Authentication required"),
    },
)
