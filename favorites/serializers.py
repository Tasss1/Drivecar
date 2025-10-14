from rest_framework import serializers
from .models import Favorite
from cars.serializers import CarSerializer


class FavoriteSerializer(serializers.ModelSerializer):
    car = CarSerializer(read_only=True)
    car_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = Favorite
        fields = ['id', 'car', 'car_id', 'created_at']

    def create(self, validated_data):
        car_id = validated_data.pop('car_id')
        user = validated_data.pop('user')
        car = Car.objects.get(id=car_id)
        return Favorite.objects.create(user=user, car=car, **validated_data)