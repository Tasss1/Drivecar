from rest_framework import serializers
from api.models import User
from django.contrib.auth.password_validation import validate_password


class UserSerializer(serializers.ModelSerializer):
    """Сериализатор для отображения данных пользователя."""
    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name']
        read_only_fields = ['id', 'email', 'first_name', 'last_name']


class RegisterSerializer(serializers.ModelSerializer):
    """Сериализатор для регистрации нового пользователя."""
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    password2 = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )
    name = serializers.CharField(required=True)

    class Meta:
        model = User
        fields = ['name', 'email', 'password', 'password2']

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Пароли не совпадают."})
        return attrs

    def create(self, validated_data):
        validated_data.pop('password2')
        name = validated_data.pop('name')
        email = validated_data.get('email')
        password = validated_data.get('password')

        # ✅ без username — всё корректно
        user = User.objects.create_user(
            email=email,
            first_name=name,
        )
        user.set_password(password)
        user.save()
        return user