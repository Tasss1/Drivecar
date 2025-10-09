from django.urls import path
from . import auth_views

urlpatterns = [
    path('auth/register/', auth_views.register, name='register'),
    path('auth/login/', auth_views.login, name='login'),
    path('auth/refresh/', auth_views.refresh_token, name='refresh'),
    path('auth/verify-email/', auth_views.verify_email, name='verify-email'),
    path('auth/profile/', auth_views.profile, name='profile'),
    path('auth/logout/', auth_views.logout, name='logout'),
]