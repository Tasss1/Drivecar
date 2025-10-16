from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

user_router = DefaultRouter()
user_router.register(r'', views.CarViewSet, basename='car')  # /api/v1/cars/

admin_router = DefaultRouter()
admin_router.register(r'cars', views.AdminCarViewSet, basename='admin-car')  # /api/v1/cars/admin/cars/

urlpatterns = [
    path('', include(user_router.urls)),
    path('admin/', include(admin_router.urls)),
]
