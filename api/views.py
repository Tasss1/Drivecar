from django.contrib.auth import authenticate
from django.db import transaction
from rest_framework import viewsets, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.utils import timezone
import random
from datetime import timedelta

from api.models import User
from .serializers import RegisterSerializer, UserSerializer
from .tokens import CustomAccessToken
from gmail_setup import send_email


class ProfileViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'], url_path='me')
    def get_profile(self, request):
        """Получить свой профиль"""
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

    @action(detail=False, methods=['patch'], url_path='me')
    def update_profile(self, request):
        """Обновить профиль"""
        serializer = UserSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AuthViewSet(viewsets.ViewSet):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_summary="Регистрация",
        operation_description="Создаёт аккаунт и отправляет код подтверждения на email.",
        request_body=RegisterSerializer,
        responses={
            201: openapi.Response('Успех', examples={'application/json': {'message': 'Регистрация успешна. Проверьте email.'}}),
            400: 'Ошибки валидации',
            500: 'Ошибка отправки письма'
        },
        tags=['auth']
    )
    @action(detail=False, methods=['post'], url_path='register')
    def register(self, request):
        serializer = RegisterSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            with transaction.atomic():
                user = serializer.save()
                user.is_active = False
                user.activation_key = f"{random.randint(0, 9999):04d}"
                user.activation_key_expires = timezone.now() + timedelta(hours=48)
                user.password_reset_confirmed = False
                user.save()

                self.send_activation_email(user)

            return Response({'message': 'Регистрация успешна. Проверьте email.'}, status=status.HTTP_201_CREATED)

        except Exception as e:
            print(f"Ошибка при регистрации (откат): {e}")
            return Response({'message': 'Ошибка при отправке письма. Попробуйте позже.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @swagger_auto_schema(
        operation_summary="Вход",
        operation_description="Авторизация по email и паролю.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'email': openapi.Schema(type=openapi.TYPE_STRING, format='email', example='user@example.com'),
                'password': openapi.Schema(type=openapi.TYPE_STRING, format='password', example='mypassword123')
            },
            required=['email', 'password']
        ),
        responses={
            200: openapi.Response('Успех', examples={'application/json': {
                'access': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.xxxx',
                'role': 'user'
            }})
        },
        tags=['auth']
    )
    @action(detail=False, methods=['post'], url_path='login')
    def login(self, request):
        email = request.data.get('email')
        password = request.data.get('password')

        if not email or not password:
            return Response({'message': 'Email и пароль обязательны'}, status=status.HTTP_400_BAD_REQUEST)

        user = authenticate(username=email, password=password)
        if not user:
            return Response({'message': 'Неверные данные'}, status=status.HTTP_400_BAD_REQUEST)

        if not user.is_active:
            return Response({'message': 'Аккаунт не активирован'}, status=status.HTTP_400_BAD_REQUEST)

        access = str(CustomAccessToken.for_user(user))
        role = "admin" if user.is_staff or user.is_superuser else "user"
        return Response({'access': access, 'role': role}, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_summary="Подтвердить email",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'email': openapi.Schema(type=openapi.TYPE_STRING, format='email', example='user@example.com'),
                'code': openapi.Schema(type=openapi.TYPE_STRING, example='0423')
            },
            required=['email', 'code']
        ),
        tags=['auth']
    )
    @action(detail=False, methods=['post'], url_path='verify-email')
    def verify_email(self, request):
        email = request.data.get('email')
        code = request.data.get('code')

        if not email or not code:
            return Response({'message': 'Email и код обязательны'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=email, is_active=False)
            if user.activation_key == code and user.activation_key_expires > timezone.now():
                user.is_active = True
                user.activation_key = None
                user.activation_key_expires = None
                user.save()

                access = str(CustomAccessToken.for_user(user))
                role = "admin" if user.is_staff or user.is_superuser else "user"
                return Response({'message': 'Email подтверждён', 'access': access, 'role': role})
            return Response({'message': 'Неверный или просроченный код'}, status=status.HTTP_400_BAD_REQUEST)
        except User.DoesNotExist:
            return Response({'message': 'Пользователь не найден или уже активирован'}, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        operation_summary="Забыл пароль — отправить код",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={'email': openapi.Schema(type=openapi.TYPE_STRING, format='email', example='user@example.com')},
            required=['email']
        ),
        tags=['auth', 'password']
    )
    @action(detail=False, methods=['post'], url_path='password/reset/request')
    def password_reset_request(self, request):
        email = request.data.get('email')
        if not email:
            return Response({'message': 'Email обязателен'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=email)

            try:
                with transaction.atomic():
                    user.activation_key = f"{random.randint(0, 9999):04d}"
                    user.activation_key_expires = timezone.now() + timedelta(hours=1)
                    user.password_reset_confirmed = False
                    user.save()

                    self.send_reset_email(user)  # Если ошибка — откат

                return Response({'message': 'Код отправлен на email'}, status=status.HTTP_200_OK)

            except Exception as e:
                print(f"Ошибка отправки кода сброса: {e}")
                return Response({'message': 'Ошибка при отправке кода. Попробуйте позже.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        except User.DoesNotExist:
            return Response({'message': 'Код отправлен на email'}, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_summary="Подтвердить код сброса",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'email': openapi.Schema(type=openapi.TYPE_STRING, format='email', example='user@example.com'),
                'code': openapi.Schema(type=openapi.TYPE_STRING, example='0423')
            },
            required=['email', 'code']
        ),
        tags=['auth', 'password']
    )
    @action(detail=False, methods=['post'], url_path='password/reset/verify-code')
    def password_reset_verify_code(self, request):
        email = request.data.get('email')
        code = request.data.get('code')

        if not email or not code:
            return Response({'message': 'Email и код обязательны'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=email)
            if user.activation_key == code and user.activation_key_expires > timezone.now():
                user.password_reset_confirmed = True
                user.save()
                return Response({'message': 'Код подтверждён. Введите новый пароль.'}, status=status.HTTP_200_OK)
            return Response({'message': 'Неверный или просроченный код'}, status=status.HTTP_400_BAD_REQUEST)
        except User.DoesNotExist:
            return Response({'message': 'Неверный запрос'}, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        operation_summary="Сменить пароль",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'email': openapi.Schema(type=openapi.TYPE_STRING, format='email', example='user@example.com'),
                'new_password': openapi.Schema(type=openapi.TYPE_STRING, example='NewPass123!')
            },
            required=['email', 'new_password']
        ),
        tags=['auth', 'password']
    )
    @action(detail=False, methods=['post'], url_path='password/reset/complete')
    def password_reset_complete(self, request):
        email = request.data.get('email')
        new_password = request.data.get('new_password')

        if not email or not new_password:
            return Response({'message': 'Email и новый пароль обязательны'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=email)
            if user.password_reset_confirmed and user.activation_key_expires > timezone.now():
                user.set_password(new_password)
                user.activation_key = None
                user.activation_key_expires = None
                user.password_reset_confirmed = False
                user.save()
                return Response({'message': 'Пароль успешно изменён!'}, status=status.HTTP_200_OK)
            return Response({'message': 'Код не подтверждён или срок истёк'}, status=status.HTTP_400_BAD_REQUEST)
        except User.DoesNotExist:
            return Response({'message': 'Неверный запрос'}, status=status.HTTP_400_BAD_REQUEST)

    def send_activation_email(self, user):
        send_email(
            to=user.email,
            subject='Активация аккаунта',
            body=f'Код подтверждения: {user.activation_key}\nДействителен 48 часов.'
        )

    def send_reset_email(self, user):
        send_email(
            to=user.email,
            subject='Сброс пароля',
            body=f'Код для сброса: {user.activation_key}\nДействителен 1 час.'
        )
