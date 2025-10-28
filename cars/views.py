from rest_framework import permissions
from rest_framework.parsers import MultiPartParser, FormParser
from .models import Ad, CarImage
from .serializers import AdSerializer, CarSerializer, CarCreateSerializer, CarImageSerializer
from rest_framework import viewsets, status
from rest_framework.permissions import IsAdminUser, IsAuthenticatedOrReadOnly, IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.db.models import Q, Count
from .models import Car
from favorites.models import Favorite


class AdminCarViewSet(viewsets.ModelViewSet):
    """
    Управление машинами (только для админа)
    """
    queryset = Car.objects.all()
    permission_classes = [IsAdminUser]
    parser_classes = [MultiPartParser, FormParser]

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return CarCreateSerializer
        return CarSerializer

    @swagger_auto_schema(
        operation_summary="Список машин (админ)",
        operation_description="Получить список всех машин с фильтрацией по бренду, модели, цене и статусу",
        manual_parameters=[
            openapi.Parameter('search', openapi.IN_QUERY, description="Поиск по бренду или модели",
                              type=openapi.TYPE_STRING),
            openapi.Parameter('is_active', openapi.IN_QUERY, description="Фильтр по статусу (активна/не активна)",
                              type=openapi.TYPE_BOOLEAN),
            openapi.Parameter('min_price', openapi.IN_QUERY, description="Минимальная цена", type=openapi.TYPE_NUMBER),
            openapi.Parameter('max_price', openapi.IN_QUERY, description="Максимальная цена", type=openapi.TYPE_NUMBER),
        ],
        tags=['Админ Машины']
    )
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        search = request.query_params.get('search')
        if search:
            queryset = queryset.filter(Q(brand__icontains=search) | Q(model__icontains=search))
        is_active = request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=bool(int(is_active)))
        min_price = request.query_params.get('min_price')
        if min_price:
            queryset = queryset.filter(price__gte=min_price)
        max_price = request.query_params.get('max_price')
        if max_price:
            queryset = queryset.filter(price__lte=max_price)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_summary="Создать машину (админ)",
        operation_description="Создать новую машину с указанием всех полей",
        request_body=CarCreateSerializer,
        tags=['Админ Машины']
    )
    def create(self, request, *args, **kwargs):
        images_data = request.FILES.getlist('images')
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        car = serializer.save()

        # сохраняем до 10 дополнительных фото
        for img in images_data[:10]:
            CarImage.objects.create(car=car, image=img)

        full_serializer = CarSerializer(car, context=self.get_serializer_context())
        return Response(full_serializer.data, status=status.HTTP_201_CREATED)

    @swagger_auto_schema(
        operation_summary="Получить машину (админ)",
        operation_description="Получить информацию о машине по ID",
        tags=['Админ Машины']
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Редактировать машину (админ)",
        operation_description="Обновить все поля машины по ID",
        request_body=CarCreateSerializer,
        tags=['Админ Машины']
    )
    def update(self, request, *args, **kwargs):
        car = self.get_object()
        images_data = request.FILES.getlist('images')
        serializer = self.get_serializer(car, data=request.data, partial=False)
        serializer.is_valid(raise_exception=True)
        car = serializer.save()

        if images_data:
            car.images.all().delete()
            for img in images_data[:10]:
                CarImage.objects.create(car=car, image=img)

        full_serializer = CarSerializer(car, context=self.get_serializer_context())
        return Response(full_serializer.data)

    @swagger_auto_schema(
        operation_summary="Частичное редактирование машины (админ)",
        operation_description="Обновить отдельные поля машины по ID",
        request_body=CarCreateSerializer,
        tags=['Админ Машины']
    )
    def partial_update(self, request, *args, **kwargs):
        car = self.get_object()
        images_data = request.FILES.getlist('images')
        serializer = self.get_serializer(car, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        car = serializer.save()

        if images_data:
            car.images.all().delete()
            for img in images_data[:10]:
                CarImage.objects.create(car=car, image=img)

        full_serializer = CarSerializer(car, context=self.get_serializer_context())
        return Response(full_serializer.data)

    @swagger_auto_schema(
        operation_summary="Удалить машину (админ)",
        operation_description="Удалить машину по ID",
        tags=['Админ Машины']
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)


class CarViewSet(viewsets.ReadOnlyModelViewSet):  # Только чтение!
    queryset = Car.objects.filter(is_active=True)
    serializer_class = CarSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        queryset = Car.objects.filter(is_active=True)

        brand = self.request.query_params.get('brand')
        if brand:
            queryset = queryset.filter(brand__icontains=brand)

        car_type = self.request.query_params.get('car_type')
        if car_type:
            queryset = queryset.filter(car_type=car_type)

        min_price = self.request.query_params.get('min_price')
        max_price = self.request.query_params.get('max_price')
        if min_price:
            queryset = queryset.filter(price__gte=min_price)
        if max_price:
            queryset = queryset.filter(price__lte=max_price)

        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(brand__icontains=search) | Q(model__icontains=search)
            )

        return queryset

    @swagger_auto_schema(
        operation_summary="Список всех машин",
        operation_description="Возвращает список всех активных машин с фильтрацией",
        manual_parameters=[
            openapi.Parameter('brand', openapi.IN_QUERY, description="Фильтр по марке", type=openapi.TYPE_STRING),
            openapi.Parameter('car_type', openapi.IN_QUERY, description="Фильтр по типу кузова",
                              type=openapi.TYPE_STRING),
            openapi.Parameter('min_price', openapi.IN_QUERY, description="Минимальная цена", type=openapi.TYPE_NUMBER),
            openapi.Parameter('max_price', openapi.IN_QUERY, description="Максимальная цена", type=openapi.TYPE_NUMBER),
            openapi.Parameter('search', openapi.IN_QUERY, description="Поиск по марке/модели",
                              type=openapi.TYPE_STRING),
        ],
        tags=['Cars']
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Получение информации о машине",
        operation_description="Возвращает данные конкретной машины по ID",
        responses={200: CarSerializer()},
        tags=['Cars']
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Рекомендуемые машины",
        operation_description="Получить рекомендуемые машины для главной страницы (новые и популярные)",
        tags=['Cars']
    )
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticatedOrReadOnly])
    def featured(self, request):
        new_cars = Car.objects.filter(is_active=True).order_by('-created_at')[:6]
        popular_cars = Car.objects.filter(is_active=True).annotate(
            favorites_count=Count('favorite')
        ).order_by('-favorites_count')[:6]

        new_serializer = CarSerializer(new_cars, many=True, context={'request': request})
        popular_serializer = CarSerializer(popular_cars, many=True, context={'request': request})

        return Response({
            'new_cars': new_serializer.data,
            'popular_cars': popular_serializer.data
        })

    @swagger_auto_schema(
        operation_summary="Получить бренды",
        operation_description="Получить все доступные бренды машин",
        tags=['Cars']
    )
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticatedOrReadOnly])
    def brands(self, request):
        brands = Car.objects.filter(is_active=True).values_list('brand', flat=True).distinct()
        return Response({'brands': list(brands)})

    @swagger_auto_schema(
        operation_summary="Получить типы кузова",
        operation_description="Получить все доступные типы кузова",
        tags=['Cars']
    )
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticatedOrReadOnly])
    def car_types(self, request):
        car_types = [choice[0] for choice in Car.CAR_TYPES]
        return Response({'car_types': car_types})

    @swagger_auto_schema(
        operation_summary="Получить изображения машины",
        operation_description="Получить все дополнительные изображения машины",
        tags=['Cars']
    )
    @action(detail=True, methods=['get'])
    def images(self, request, pk=None):
        car = self.get_object()
        images = car.images.all()
        serializer = CarImageSerializer(images, many=True)
        return Response(serializer.data)


class AdViewSet(viewsets.ModelViewSet):
    queryset = Ad.objects.all()
    serializer_class = AdSerializer
    permission_classes = [IsAdminUser]  # Только админ!
    parser_classes = [MultiPartParser, FormParser]

    @swagger_auto_schema(
        operation_summary="Список рекламных объявлений",
        operation_description="Получить все рекламные объявления",
        tags=['Ads']
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Получить рекламное объявление",
        operation_description="Получить информацию о рекламном объявлении по ID",
        tags=['Ads']
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

