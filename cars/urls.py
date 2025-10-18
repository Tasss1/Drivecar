from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# ======= User endpoints =======
user_router = DefaultRouter()
user_router.register(r'cars', views.CarViewSet, basename='user-cars')  # /api/v1/cars/
user_router.register(r'ads', views.AdViewSet, basename='ads')           # /api/v1/ads/

# ======= Admin endpoints =======
admin_router = DefaultRouter()
admin_router.register(r'cars', views.AdminCarViewSet, basename='admin-cars')  # /api/v1/admin/cars/

urlpatterns = [
    # --- User block ---
    path('', include(user_router.urls)),

    # --- Admin block ---
    path('admin/', include(admin_router.urls)),
]