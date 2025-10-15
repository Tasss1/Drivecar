from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from django.contrib.auth import authenticate
import random
from datetime import timedelta

from api.models import User
from .serializers import RegisterSerializer
from .tokens import CustomAccessToken


class AuthViewSet(viewsets.ViewSet):
    permission_classes = [AllowAny]

    # === Регистрация ===
    @swagger_auto_schema(
        operation_summary="Register",
        operation_description="Создаёт новый аккаунт пользователя и отправляет код подтверждения на email.",
        request_body=RegisterSerializer,
        responses={201: openapi.Response(
            'Success',
            examples={'application/json': {'message': 'Регистрация успешна. Проверьте email.'}}
        )},
        tags=['auth']
    )
    @action(detail=False, methods=['post'], url_path='register')
    def register(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            user.is_active = False
            user.activation_key = ''.join([str(random.randint(0, 9)) for _ in range(4)])
            user.activation_key_expires = timezone.now() + timedelta(hours=48)
            user.save()
            self.send_activation_email(user)
            return Response({'message': 'Регистрация успешна. Проверьте email.'}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # === Логин ===
    @swagger_auto_schema(
        operation_summary="Login",
        operation_description="Авторизация по email и паролю. Возвращает JWT токен с ролью.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'email': openapi.Schema(type=openapi.TYPE_STRING, format='email'),
                'password': openapi.Schema(type=openapi.TYPE_STRING),
            },
            required=['email', 'password']
        ),
        responses={
            200: openapi.Response(
                description="JWT access token",
                examples={'application/json': {'access': 'JWT_ACCESS_TOKEN', 'role': 'user'}}
            ),
            400: openapi.Response(description="Bad Request"),
        },
        tags=['auth']
    )
    @action(detail=False, methods=['post'], url_path='login')
    def login(self, request):
        email = request.data.get('email')
        password = request.data.get('password')

        if not email or '@' not in email or '.' not in email.split('@')[-1]:
            return Response({'message': 'Неверный email'}, status=status.HTTP_400_BAD_REQUEST)

        user = authenticate(username=email, password=password)
        if not user:
            return Response({'message': 'Неверные данные'}, status=status.HTTP_400_BAD_REQUEST)

        if not user.is_active:
            return Response({'message': 'Аккаунт не активирован'}, status=status.HTTP_400_BAD_REQUEST)

        # ✅ Генерация кастомного токена с ролью
        access = str(CustomAccessToken.for_user(user))
        role = "admin" if user.is_staff or user.is_superuser else "user"

        return Response({'access': access, 'role': role}, status=status.HTTP_200_OK)

# === Подтверждение Email ===
    @swagger_auto_schema(
        operation_summary="Verify Email",
        operation_description="Подтверждает email по коду из письма и активирует аккаунт.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'email': openapi.Schema(type=openapi.TYPE_STRING, format='email'),
                'code': openapi.Schema(type=openapi.TYPE_STRING)
            },
            required=['email', 'code']
        ),
        tags=['auth']
    )
    @action(detail=False, methods=['post'], url_path='verify-email')
    def verify_email(self, request):
        email = request.data.get('email')
        code = request.data.get('code')

        try:
            user = User.objects.get(email=email, is_active=False)
            if user.activation_key == code and user.activation_key_expires > timezone.now():
                user.is_active = True
                user.save()

                access = str(CustomAccessToken.for_user(user))
                role = "admin" if user.is_staff or user.is_superuser else "user"

                return Response({'message': 'Email подтверждён', 'access': access, 'role': role})
            return Response({'message': 'Неверный код или срок истёк'}, status=status.HTTP_400_BAD_REQUEST)
        except User.DoesNotExist:
            return Response({'message': 'Пользователь не найден'}, status=status.HTTP_400_BAD_REQUEST)

    # === Забыл пароль ===
    @swagger_auto_schema(
        operation_summary="Forgot Password",
        operation_description="Отправляет 4-значный код для сброса пароля на email.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'email': openapi.Schema(type=openapi.TYPE_STRING, format='email'),
            },
            required=['email']
        ),
        tags=['auth']
    )
    @action(detail=False, methods=['post'], url_path='forgot-password')
    def forgot_password(self, request):
        email = request.data.get('email')
        try:
            user = User.objects.get(email=email)
            user.activation_key = ''.join([str(random.randint(0, 9)) for _ in range(4)])
            user.activation_key_expires = timezone.now() + timedelta(hours=1)
            user.save()
            self.send_reset_email(user)
            return Response({'message': 'Код отправлен на email.'}, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({'message': 'Email не найден'}, status=status.HTTP_400_BAD_REQUEST)

    # === Сброс пароля ===
    @swagger_auto_schema(
        operation_summary="Reset Password",
        operation_description="Сбрасывает пароль с использованием кода, отправленного на email.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'email': openapi.Schema(type=openapi.TYPE_STRING, format='email'),
                'code': openapi.Schema(type=openapi.TYPE_STRING),
                'new_password': openapi.Schema(type=openapi.TYPE_STRING),
            },
            required=['email', 'code', 'new_password']
        ),
        tags=['auth']
    )
    @action(detail=False, methods=['post'], url_path='reset-password')
    def reset_password(self, request):
        email = request.data.get('email')
        code = request.data.get('code')
        new_password = request.data.get('new_password')

        try:
            user = User.objects.get(email=email)
            if user.activation_key == code and user.activation_key_expires > timezone.now():
                user.set_password(new_password)
                user.save()
                return Response({'message': 'Пароль изменён'}, status=status.HTTP_200_OK)
            return Response({'message': 'Неверный код или срок истёк'}, status=status.HTTP_400_BAD_REQUEST)
        except User.DoesNotExist:
            return Response({'message': 'Email не найден'}, status=status.HTTP_400_BAD_REQUEST)

# === Email-помощники ===
    def send_activation_email(self, user):
        send_mail(
            'Активация аккаунта',
            f'Ваш код подтверждения: {user.activation_key}',
            settings.DEFAULT_FROM_EMAIL,
            [user.email]
        )

    def send_reset_email(self, user):
        send_mail(
            'Сброс пароля',
            f'Ваш код для сброса: {user.activation_key}',
            settings.DEFAULT_FROM_EMAIL,
            [user.email]
        )