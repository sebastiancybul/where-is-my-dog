from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate

from ..serializers import UserSerializer, RegistrationSerializer
from ..schemas import register_schema, login_schema, current_user_schema


@register_schema
@api_view(["POST"])
@permission_classes([AllowAny])
def register(request):
    """Register a new user account"""

    serializer = RegistrationSerializer(data=request.data)

    if serializer.is_valid():
        user = serializer.save()
    else:
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    refresh = RefreshToken.for_user(user)

    tokens = {
        "refresh": str(refresh),
        "access": str(refresh.access_token),
    }

    return Response(
        {"user": UserSerializer(user).data, "tokens": tokens},
        status=status.HTTP_201_CREATED,
    )


@login_schema
@api_view(["POST"])
@permission_classes([AllowAny])
def login(request):
    """Login user and return JWT tokens"""

    email = request.data.get("email")
    password = request.data.get("password")

    user = authenticate(email=email, password=password)

    if user is None:
        return Response(
            {"error": "Invalid credentials"},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    refresh = RefreshToken.for_user(user)

    tokens = {"refresh": str(refresh), "access": str(refresh.access_token)}

    return Response({"user": UserSerializer(user).data, "tokens": tokens})


@current_user_schema
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def current_user(request):
    """Get current logged-in user"""

    return Response(UserSerializer(request.user).data)
