from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/auth/', include('api.urls')),
    path('api/v1/cars/', include('cars.urls')),
    path('api/v1/favorites/', include('favorites.urls')),

    # Swagger/OpenAPI документация
    path('swagger/', SpectacularSwaggerView.as_view(url_name='schema'), name='schema-swagger-ui'),
    path('redoc/', SpectacularRedocView.as_view(url_name='schema'), name='schema-redoc'),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
]