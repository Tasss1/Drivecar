# cars/serializers.py
from rest_framework import serializers
from .models import Car, CarImage, Ad
from favorites.models import Favorite


class CarImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = CarImage
        fields = ['id', 'image']


class CarSerializer(serializers.ModelSerializer):
    images = CarImageSerializer(many=True, read_only=True)
    is_favorite = serializers.SerializerMethodField()
    installment_months = serializers.SerializerMethodField()

    class Meta:
        model = Car
        fields = [
            'id', 'brand', 'model', 'year', 'price', 'car_type', 'fuel_type',
            'engine_volume', 'power', 'transmission', 'mileage', 'condition',
            'steering', 'color', 'installment', 'phone', 'image', 'description',
            'images', 'created_at', 'is_active', 'views', 'is_favorite', 'installment_months'
        ]
        read_only_fields = ['images', 'views', 'created_at']

    def get_is_favorite(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Favorite.objects.filter(user=request.user, car=obj).exists()
        return False

    def get_installment_months(self, obj):
        return [6, 9, 12] if obj.installment else []


class CarCreateSerializer(serializers.ModelSerializer):
    # Доп. фото — список файлов
    images = serializers.ListField(
        child=serializers.ImageField(),
        write_only=True,
        required=False,
        max_length=10
    )

    class Meta:
        model = Car
        fields = [
            'brand', 'model', 'year', 'price', 'car_type', 'fuel_type',
            'engine_volume', 'power', 'transmission', 'mileage', 'condition',
            'steering', 'color', 'installment', 'phone', 'image', 'description', 'is_active', 'images'
        ]

    def validate_phone(self, value):
        if not value:
            raise serializers.ValidationError("Телефон обязателен.")
        return value

    def validate_year(self, value):
        from datetime import date
        current_year = date.today().year
        if value < 1900 or value > current_year + 1:
            raise serializers.ValidationError(f"Год должен быть от 1900 до {current_year + 1}")
        return value


class AdSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ad
        fields = '__all__'