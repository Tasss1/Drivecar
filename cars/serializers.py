from rest_framework import serializers
from .models import Car, CarImage, Ad
from favorites.models import Favorite


class CarImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = CarImage
        fields = ['id', 'image']


class CarSerializer(serializers.ModelSerializer):
    images = CarImageSerializer(many=True, read_only=True)
    image = serializers.ImageField(required=False)
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
            # Проверка для Swagger
            if getattr(self, 'swagger_fake_view', False):
                return False
            from favorites.models import Favorite
            return Favorite.objects.filter(user=request.user, car=obj).exists()
        return False

    def get_installment_months(self, obj):
        if obj.installment:
            return [6, 9, 12]
        return []


class CarCreateSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(required=False)

    class Meta:
        model = Car
        fields = [
            'brand', 'model', 'year', 'price', 'car_type', 'fuel_type',
            'engine_volume', 'power', 'transmission', 'mileage', 'condition',
            'steering', 'color', 'installment', 'phone', 'image', 'description', 'is_active'
        ]


class AdSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ad
        fields = '__all__'