from django.contrib import admin
from django.urls import path, include
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from django.conf import settings
from django.conf.urls.static import static

# Swagger / OpenAPI
schema_view = get_schema_view(
    openapi.Info(
        title="AUTO API",
        default_version='v1',
        description="API для автомобильной платформы AUTO",
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
)

urlpatterns = [
    path('admin/', admin.site.urls),

    # API маршруты
    path('api/v1/auth/', include('api.urls')),
    path('api/v1/cars/', include('cars.urls')),
    path('api/v1/favorites/', include('favorites.urls')),
    path('api/v1/banner/', include('banner.urls')),
    # Swagger UI
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]

# Статика и медиа (только для DEBUG режима)
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

