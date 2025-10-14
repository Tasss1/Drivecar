from rest_framework import serializers
from .models import Car

class CarSerializer(serializers.ModelSerializer):
    is_favorite = serializers.SerializerMethodField()
    is_active = serializers.BooleanField(read_only=True)  # Добавлено для admin

    class Meta:
        model = Car
        fields = ['id', 'brand', 'model', 'year', 'price', 'car_type',
                  'fuel_type', 'engine_volume', 'power', 'image',
                  'description', 'is_favorite', 'created_at', 'is_active']

    def get_is_favorite(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            from favorites.models import Favorite
            return Favorite.objects.filter(user=request.user, car=obj).exists()
        return False