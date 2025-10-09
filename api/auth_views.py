from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth.models import User
from .serializers import UserSerializer, RegisterSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from drf_yasg.utils import swagger_auto_schema

@swagger_auto_schema(method='post', operation_summary="Register", tags=['auth'])
@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    """Register new user"""
    serializer = RegisterSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        return Response({
            'user': UserSerializer(user).data,
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@swagger_auto_schema(method='post', operation_summary="Login", tags=['auth'])
@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    """Login user"""
    return TokenObtainPairView.as_view()(request)

@swagger_auto_schema(method='post', operation_summary="Refresh Token", tags=['auth'])
@api_view(['POST'])
@permission_classes([AllowAny])
def refresh_token(request):
    """Refresh token"""
    return TokenRefreshView.as_view()(request)

@swagger_auto_schema(method='post', operation_summary="Verify Email", tags=['auth'])
@api_view(['POST'])
@permission_classes([AllowAny])
def verify_email(request):
    """Verify email"""
    return Response({'message': 'Email verification endpoint'})

@swagger_auto_schema(method='get', operation_summary="Get Profile", tags=['auth'])
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def profile(request):
    """Get user profile"""
    serializer = UserSerializer(request.user)
    return Response(serializer.data)

@swagger_auto_schema(method='post', operation_summary="Logout", tags=['auth'])
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout(request):
    """Logout user"""
    return Response({'message': 'Successfully logged out'})