from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from shop.serializers import (
    AuthResponseSerializer,
    LoginSerializer,
    PendingUserResponseSerializer,
    RefreshTokenSerializer,
    SimpleRegisterSerializer,
)
from shop.services import AuthService


@extend_schema(
    tags=["Auth"],
    summary="Register new user",
    description="Register a new user without company affiliation. User will be pending until linked to a company.",
    request=SimpleRegisterSerializer,
    responses={200: PendingUserResponseSerializer, 400: None},
)
@api_view(["POST"])
@permission_classes([AllowAny])
def simple_register(request):
    serializer = SimpleRegisterSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    try:
        result = AuthService.simple_register(serializer.validated_data)
        return Response(PendingUserResponseSerializer(result).data)
    except ValueError as e:
        return Response({"message": str(e)}, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    tags=["Auth"],
    summary="User login",
    description="Authenticate user with email and password. Returns JWT tokens.",
    request=LoginSerializer,
    responses={200: AuthResponseSerializer, 401: None},
)
@api_view(["POST"])
@permission_classes([AllowAny])
def login(request):
    serializer = LoginSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    try:
        result = AuthService.login(serializer.validated_data)
        return Response(AuthResponseSerializer(result).data)
    except PermissionError:
        return Response(
            "Invalid email or password.",
            status=status.HTTP_401_UNAUTHORIZED,
        )
    except Exception:
        return Response(
            "An error occurred while logging in.",
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@extend_schema(
    tags=["Auth"],
    summary="Refresh access token",
    description="Get new access token using refresh token.",
    request=RefreshTokenSerializer,
    responses={200: AuthResponseSerializer, 400: None},
)
@api_view(["POST"])
@permission_classes([AllowAny])
def refresh_token(request):
    serializer = RefreshTokenSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    try:
        result = AuthService.refresh_token(serializer.validated_data["refresh_token"])
        return Response(AuthResponseSerializer(result).data)
    except ValueError as e:
        return Response(str(e), status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    tags=["Auth"],
    summary="Revoke user token",
    description="Invalidate user's refresh token to log them out.",
    responses={200: None, 400: None},
)
@api_view(["POST"])
@permission_classes([AllowAny])
def revoke_token(request):
    user_id = request.data if isinstance(request.data, str) else request.data.get("user_id", "")
    try:
        result = AuthService.revoke_token(user_id)
        if result:
            return Response(status=status.HTTP_200_OK)
        return Response("User not found.", status=status.HTTP_400_BAD_REQUEST)
    except Exception:
        return Response(
            "An error occurred while revoking token.",
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
