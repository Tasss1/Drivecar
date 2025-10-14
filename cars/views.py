from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.db.models import Q, Count
from .models import Car
from .serializers import CarSerializer


class CarViewSet(viewsets.ModelViewSet):
    queryset = Car.objects.all()
    serializer_class = CarSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    @swagger_auto_schema(
        operation_summary="Get All Cars",
        operation_description="Get paginated list of cars with filtering and search",
        manual_parameters=[
            openapi.Parameter('brand', openapi.IN_QUERY, description="Filter by brand", type=openapi.TYPE_STRING),
            openapi.Parameter('car_type', openapi.IN_QUERY, description="Filter by car type", type=openapi.TYPE_STRING),
            openapi.Parameter('min_price', openapi.IN_QUERY, description="Minimum price", type=openapi.TYPE_NUMBER),
            openapi.Parameter('max_price', openapi.IN_QUERY, description="Maximum price", type=openapi.TYPE_NUMBER),
            openapi.Parameter('search', openapi.IN_QUERY, description="Search by brand or model",
                              type=openapi.TYPE_STRING),
            openapi.Parameter('page', openapi.IN_QUERY, description="Page number", type=openapi.TYPE_INTEGER),
        ],
        tags=['Cars']
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Get Car Details",
        operation_description="Get detailed information about a specific car",
        tags=['Cars']
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Create Car",
        operation_description="Create a new car (Admin only)",
        request_body=CarSerializer,
        tags=['Cars']
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Add to Favorites",
        operation_description="Add a car to user's favorites",
        responses={
            201: openapi.Response('Success', examples={
                'application/json': {'status': 'added to favorites'}
            }),
            200: openapi.Response('Info', examples={
                'application/json': {'status': 'already in favorites'}
            })
        },
        tags=['Cars']
    )
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def add_to_favorites(self, request, pk=None):
        car = self.get_object()
        from favorites.models import Favorite
        favorite, created = Favorite.objects.get_or_create(
            user=request.user, car=car
        )
        if created:
            return Response({
                'message': 'Автомобиль добавлен в избранное',
                'status': 'added to favorites'
            }, status=status.HTTP_201_CREATED)
        return Response({
            'message': 'Автомобиль уже в избранном',
            'status': 'already in favorites'
        }, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_summary="Remove from Favorites",
        operation_description="Remove a car from user's favorites",
        responses={
            200: openapi.Response('Success', examples={
                'application/json': {'status': 'removed from favorites'}
            })
        },
        tags=['Cars']
    )
    @action(detail=True, methods=['delete'], permission_classes=[IsAuthenticated])
    def remove_from_favorites(self, request, pk=None):
        car = self.get_object()
        from favorites.models import Favorite
        Favorite.objects.filter(user=request.user, car=car).delete()
        return Response({
            'message': 'Автомобиль удален из избранного',
            'status': 'removed from favorites'
        }, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_summary="Featured Cars",
        operation_description="Get featured cars for homepage (new and popular)",
        tags=['Cars']
    )
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticatedOrReadOnly])
    def featured(self, request):
        new_cars = Car.objects.all().order_by('-created_at')[:6]
        popular_cars = Car.objects.annotate(
            favorites_count=Count('favorite')
        ).order_by('-favorites_count')[:6]

        new_serializer = CarSerializer(new_cars, many=True, context={'request': request})
        popular_serializer = CarSerializer(popular_cars, many=True, context={'request': request})

        return Response({
            'new_cars': new_serializer.data,
            'popular_cars': popular_serializer.data
        })

    @swagger_auto_schema(
        operation_summary="Get Brands",
        operation_description="Get all available car brands",
        tags=['Cars']
    )
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticatedOrReadOnly])
    def brands(self, request):
        brands = Car.objects.values_list('brand', flat=True).distinct()
        return Response({'brands': list(brands)})

    @swagger_auto_schema(
        operation_summary="Get Car Types",
        operation_description="Get all available car types",
        tags=['Cars']
    )
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticatedOrReadOnly])
    def car_types(self, request):
        car_types = [choice[0] for choice in Car.CAR_TYPES]
        return Response({'car_types': car_types})

    def get_queryset(self):
        queryset = Car.objects.all()

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