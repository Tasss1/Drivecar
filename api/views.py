from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth.models import User
from .serializers import UserSerializer, RegisterSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from drf_yasg.utils import swagger_auto_schema


class AuthViewSet(viewsets.ViewSet):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_summary="Register",
        operation_description="Create new user account",
        tags=['auth']
    )
    @action(detail=False, methods=['post'], permission_classes=[AllowAny], url_path='register')
    def register(self, request):
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

    @swagger_auto_schema(
        operation_summary="Login",
        operation_description="Get JWT token",
        tags=['auth']
    )
    @action(detail=False, methods=['post'], permission_classes=[AllowAny], url_path='login')
    def login(self, request):
        """Login user and get tokens"""
        # Используем стандартный JWT login
        return TokenObtainPairView.as_view()(request._request)

    @swagger_auto_schema(
        operation_summary="Refresh Token",
        operation_description="Refresh JWT token",
        tags=['auth']
    )
    @action(detail=False, methods=['post'], permission_classes=[AllowAny], url_path='refresh')
    def refresh(self, request):
        """Refresh JWT token"""
        return TokenRefreshView.as_view()(request._request)

    @swagger_auto_schema(
        operation_summary="Verify Email",
        operation_description="Verify user email",
        tags=['auth']
    )
    @action(detail=False, methods=['post'], permission_classes=[AllowAny], url_path='verify-email')
    def verify_email(self, request):
        """Verify email address"""
        # Заглушка для верификации email
        return Response({'message': 'Email verification endpoint'})

    @swagger_auto_schema(
        operation_summary="Get Profile",
        operation_description="Get current user profile",
        tags=['auth']
    )
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated], url_path='profile')
    def profile(self, request):
        """Get user profile"""
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_summary="Logout",
        operation_description="Logout user",
        tags=['auth']
    )
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated], url_path='logout')
    def logout(self, request):
        """Logout user"""
        return Response({'message': 'Successfully logged out'})


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

@api_view(['POST'])
@permission_classes([AllowAny])
def verify_email(request):
    """Verify email"""
    return Response({'message': 'Email verification endpoint'})

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def profile(request):
    """Get user profile"""
    serializer = UserSerializer(request.user)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout(request):
    """Logout user"""
    return Response({'message': 'Successfully logged out'})