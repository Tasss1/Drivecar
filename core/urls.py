from django.contrib import admin
from django.urls import path, include
from rest_framework import permissions
from rest_framework.routers import DefaultRouter
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from api.views import AuthViewSet

# Swagger
schema_view = get_schema_view(
    openapi.Info(
        title="DriveCar API",
        default_version='v1',
        description="DriveCar API Documentation",
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
)

# Роутер для API
router = DefaultRouter()
router.register(r'auth', AuthViewSet, basename='auth')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/', include(router.urls)),
    path('api/v1/cars/', include('cars.urls')),
    path('api/v1/favorites/', include('favorites.urls')),

    # Документация
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]