from rest_framework.routers import DefaultRouter
from django.urls import path, include
from .views import AuthViewSet, ProfileViewSet


router = DefaultRouter()
router.register(r'auth', AuthViewSet, basename='auth')
router.register(r'profile', ProfileViewSet, basename='profile')

urlpatterns = [
    path('', include(router.urls)),
]
