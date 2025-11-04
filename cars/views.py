# cars/views.py
from django.db.models import Q, Count
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser, IsAuthenticatedOrReadOnly
from rest_framework.parsers import MultiPartParser, FormParser
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .models import Car, CarImage, Ad
from .serializers import CarSerializer, CarCreateSerializer, CarImageSerializer, AdSerializer
from favorites.models import Favorite


class AdminCarViewSet(viewsets.ModelViewSet):
    queryset = Car.objects.all()
    permission_classes = [IsAdminUser]
    parser_classes = [MultiPartParser, FormParser]

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return CarCreateSerializer
        return CarSerializer

    @swagger_auto_schema(
        operation_summary="Список машин (админ)",
        manual_parameters=[
            openapi.Parameter('search', openapi.IN_QUERY, type=openapi.TYPE_STRING),
            openapi.Parameter('is_active', openapi.IN_QUERY, type=openapi.TYPE_BOOLEAN),
            openapi.Parameter('min_price', openapi.IN_QUERY, type=openapi.TYPE_NUMBER),
            openapi.Parameter('max_price', openapi.IN_QUERY, type=openapi.TYPE_NUMBER),
        ],
        tags=['Админ Машины']
    )
    def list(self, request, *args, **kwargs):
        qs = self.get_queryset()

        if search := request.query_params.get('search'):
            qs = qs.filter(Q(brand__icontains=search) | Q(model__icontains=search))

        # Исправлено: теперь принимает true/false/1/0
        if (is_active := request.query_params.get('is_active')) is not None:
            is_active_bool = str(is_active).lower() in ('true', '1', 'yes', 'on')
            qs = qs.filter(is_active=is_active_bool)

        if min_price := request.query_params.get('min_price'):
            qs = qs.filter(price__gte=min_price)
        if max_price := request.query_params.get('max_price'):
            qs = qs.filter(price__lte=max_price)

        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        images_data = request.FILES.getlist('images')
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        car = serializer.save()

        for img in images_data[:10]:
            CarImage.objects.create(car=car, image=img)

        return Response(CarSerializer(car, context=self.get_serializer_context()).data, status=201)

    def update(self, request, *args, **kwargs):
        return self._update_car(request, partial=False)

    def partial_update(self, request, *args, **kwargs):
        return self._update_car(request, partial=True)

    def _update_car(self, request, partial):
        car = self.get_object()
        images_data = request.FILES.getlist('images')

        serializer = self.get_serializer(car, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        car = serializer.save()

        if images_data:
            car.images.all().delete()
            for img in images_data[:10]:
                CarImage.objects.create(car=car, image=img)

        return Response(CarSerializer(car, context=self.get_serializer_context()).data)


# Остальные viewsets (CarViewSet, AdViewSet) — без изменений
class CarViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Car.objects.filter(is_active=True)
    serializer_class = CarSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        qs = Car.objects.filter(is_active=True)
        # ... (фильтры без изменений)
        return qs

    @action(detail=False, methods=['get'])
    def featured(self, request): ...
    @action(detail=False, methods=['get'])
    def brands(self, request): ...
    @action(detail=False, methods=['get'])
    def car_types(self, request): ...
    @action(detail=True, methods=['get'])
    def images(self, request, pk=None): ...


class AdViewSet(viewsets.ModelViewSet):
    queryset = Ad.objects.all()
    serializer_class = AdSerializer
    permission_classes = [IsAdminUser]
    parser_classes = [MultiPartParser, FormParser]