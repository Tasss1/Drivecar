from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .models import Favorite
from .serializers import FavoriteSerializer
from cars.models import Car


class FavoriteViewSet(viewsets.ModelViewSet):
    serializer_class = FavoriteSerializer
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Get Favorites",
        operation_description="Get user's favorite cars",
        tags=['Favorites']
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Add to Favorites",
        operation_description="Add a car to favorites by car_id",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['car_id'],
            properties={
                'car_id': openapi.Schema(
                    type=openapi.TYPE_INTEGER,
                    description='ID of the car to add to favorites'
                )
            }
        ),
        tags=['Favorites']
    )
    def create(self, request, *args, **kwargs):
        car_id = request.data.get('car_id')
        if not car_id:
            return Response({
                'error': 'car_id is required'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            car = Car.objects.get(id=car_id)
        except Car.DoesNotExist:
            return Response({
                'error': 'Автомобиль не найден'
            }, status=status.HTTP_404_NOT_FOUND)

        if Favorite.objects.filter(user=request.user, car=car).exists():
            return Response({
                'error': 'Автомобиль уже в избранном'
            }, status=status.HTTP_400_BAD_REQUEST)

        favorite = Favorite.objects.create(user=request.user, car=car)
        serializer = self.get_serializer(favorite)
        return Response({
            'message': 'Автомобиль добавлен в избранное',
            'data': serializer.data
        }, status=status.HTTP_201_CREATED)

    @swagger_auto_schema(
        operation_summary="Remove Favorite",
        operation_description="Remove a car from favorites",
        tags=['Favorites']
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)

    def get_queryset(self):
        return Favorite.objects.filter(user=self.request.user)