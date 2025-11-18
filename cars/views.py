from django.db.models import Q
from rest_framework import viewsets
from rest_framework.permissions import IsAdminUser, IsAuthenticatedOrReadOnly
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework.decorators import action

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .models import Car, CarImage, Ad
from .serializers import (
    CarSerializer,
    CarCreateSerializer,
    CarImageSerializer,
    AdSerializer
)


# ===============================================================
#                        ADMIN — CARS
# ===============================================================

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
        operation_description=(
            "Возвращает полный список машин для администраторов. "
            "Поддерживает поиск, фильтрацию по активности и диапазону цен."
        ),
        manual_parameters=[
            openapi.Parameter('search', openapi.IN_QUERY, type=openapi.TYPE_STRING,
                              description="Поиск по марке или модели"),
            openapi.Parameter('is_active', openapi.IN_QUERY, type=openapi.TYPE_BOOLEAN,
                              description="Фильтр по активности"),
            openapi.Parameter('min_price', openapi.IN_QUERY, type=openapi.TYPE_NUMBER,
                              description="Минимальная цена"),
            openapi.Parameter('max_price', openapi.IN_QUERY, type=openapi.TYPE_NUMBER,
                              description="Максимальная цена"),
        ],
        tags=['Админ Машины']
    )
    def list(self, request, *args, **kwargs):
        qs = self.get_queryset()

        if search := request.query_params.get('search'):
            qs = qs.filter(Q(brand__icontains=search) | Q(model__icontains=search))

        if (is_active := request.query_params.get('is_active')) is not None:
            is_active_bool = str(is_active).lower() in ('true', '1', 'yes', 'y')
            qs = qs.filter(is_active=is_active_bool)

        if min_price := request.query_params.get('min_price'):
            qs = qs.filter(price__gte=min_price)

        if max_price := request.query_params.get('max_price'):
            qs = qs.filter(price__lte=max_price)

        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_summary="Создать машину",
        operation_description="Создаёт новую машину. Поддерживает загрузку до 10 изображений.",
        request_body=CarCreateSerializer,
        consumes=['multipart/form-data'],
        manual_parameters=[
            openapi.Parameter(
                'images', openapi.IN_FORM, type=openapi.TYPE_FILE,
                description="Дополнительные фото (до 10 шт.)",
                required=False, collectionFormat='multi'
            ),
        ],
        tags=['Админ Машины']
    )
    def create(self, request, *args, **kwargs):
        images_data = request.FILES.getlist('images')
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        car = serializer.save()

        for img in images_data[:10]:
            CarImage.objects.create(car=car, image=img)

        return Response(CarSerializer(car, context={'request': request}).data)

    @swagger_auto_schema(
        operation_summary="Обновить машину",
        operation_description="Полностью обновляет данные машины. Все фото заменяются на новые.",
        request_body=CarCreateSerializer,
        consumes=['multipart/form-data'],
        manual_parameters=[
            openapi.Parameter(
                'images', openapi.IN_FORM, type=openapi.TYPE_FILE,
                description="Новые фото (все предыдущие удалятся)",
                required=False, collectionFormat='multi'
            )
        ],
        tags=['Админ Машины']
    )
    def update(self, request, *args, **kwargs):
        return self._update_car(request, partial=False)

    @swagger_auto_schema(
        operation_summary="Частичное обновление машины",
        operation_description="Обновляет только указанные поля. Фото также можно заменить.",
        request_body=CarCreateSerializer,
        consumes=['multipart/form-data'],
        manual_parameters=[
            openapi.Parameter(
                'images', openapi.IN_FORM, type=openapi.TYPE_FILE,
                description="Новые фото (опционально)",
                required=False, collectionFormat='multi'
            )
        ],
        tags=['Админ Машины']
    )
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

        return Response(CarSerializer(car, context={'request': request}).data)


# ===============================================================
#                        USER — CARS
# ===============================================================

class CarViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Car.objects.filter(is_active=True)
    serializer_class = CarSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        qs = Car.objects.filter(is_active=True)

        if search := self.request.query_params.get('search'):
            qs = qs.filter(Q(brand__icontains=search) | Q(model__icontains=search))

        if min_price := self.request.query_params.get('min_price'):
            qs = qs.filter(price__gte=min_price)

        if max_price := self.request.query_params.get('max_price'):
            qs = qs.filter(price__lte=max_price)

        return qs

    @swagger_auto_schema(
        operation_summary="Популярные машины",
        operation_description="Топ 10 популярных машин, сортировка по просмотрам.",
        tags=['Пользователь Машины']
    )
    @action(detail=False, methods=['get'])
    def featured(self, request):
        qs = self.get_queryset().order_by('-views')[:10]
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_summary="Список марок",
        operation_description="Возвращает уникальные марки доступных машин.",
        tags=['Пользователь Машины']
    )
    @action(detail=False, methods=['get'])
    def brands(self, request):
        brands = self.get_queryset().values_list('brand', flat=True).distinct()
        return Response(list(brands))

    @swagger_auto_schema(
        operation_summary="Список типов",
        operation_description="Возвращает доступные типы кузова.",
        tags=['Пользователь Машины']
    )
    @action(detail=False, methods=['get'])
    def car_types(self, request):
        types = self.get_queryset().values_list('car_type', flat=True).distinct()
        return Response(list(types))

    @swagger_auto_schema(
        operation_summary="Фото машины",
        operation_description="Возвращает список всех фотографий указанной машины.",
        tags=['Пользователь Машины']
    )
    @action(detail=True, methods=['get'])
    def images(self, request, pk=None):
        car = self.get_object()
        images = car.images.all()
        return Response(CarImageSerializer(images, many=True).data)


# ===============================================================
#                      ADMIN — ADS
# ===============================================================

class AdViewSet(viewsets.ModelViewSet):
    queryset = Ad.objects.all()
    serializer_class = AdSerializer
    permission_classes = [IsAdminUser]
    parser_classes = [MultiPartParser, FormParser]

    @swagger_auto_schema(
        operation_summary="Список объявлений",
        operation_description="Возвращает список всех объявлений в системе.",
        tags=['Объявления']
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Создать объявление",
        operation_description="Создаёт новое объявление.",
        request_body=AdSerializer,
        tags=['Объявления']
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Получить объявление",
        operation_description="Возвращает данные конкретного объявления.",
        tags=['Объявления']
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Обновить объявление",
        operation_description="Полностью обновляет объявление.",
        tags=['Объявления']
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Частичное обновление объявления",
        operation_description="Обновляет указанные поля объявления.",
        tags=['Объявления']
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Удалить объявление",
        operation_description="Удаляет объявление.",
        tags=['Объявления']
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)
