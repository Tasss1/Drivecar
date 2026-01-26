from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Review

User = get_user_model()


class ReviewSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)  # Показывает username/email

    # УБИРАЕМ user_id полностью! Он не нужен.
    # Пользователь берётся автоматически из request.user

    class Meta:
        model = Review
        fields = ['id', 'user', 'text', 'rating', 'created_at', 'updated_at']
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']
        extra_kwargs = {
            'rating': {'required': True},
        }

    def create(self, validated_data):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            validated_data['user'] = request.user
        else:
            raise serializers.ValidationError("Требуется авторизация.")
        return super().create(validated_data)

    def validate(self, attrs):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            raise serializers.ValidationError("Требуется авторизация для оставления отзыва.")

        # Проверка: пользователь уже оставил отзыв
        if Review.objects.filter(user=request.user).exists():
            # Если это создание (не обновление)
            if not hasattr(self, 'instance'):
                raise serializers.ValidationError("Вы уже оставили отзыв. Можно только обновить существующий.")

        return attrs
