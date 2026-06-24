from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    LoginView,
    LogoutView,
    RefreshView,
    MeView,
    UserViewSet,
    VehicleViewSet,
    UserImportView,
)

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')

urlpatterns = [
    path('auth/login/', LoginView.as_view(), name='auth-login'),
    path('auth/logout/', LogoutView.as_view(), name='auth-logout'),
    path('auth/refresh/', RefreshView.as_view(), name='auth-refresh'),
    path('users/me/', MeView.as_view(), name='user-me'),
    path('users/import/', UserImportView.as_view(), name='user-import'),
    path('', include(router.urls)),
    path(
        'users/<int:user_pk>/vehicles/',
        VehicleViewSet.as_view({'get': 'list', 'post': 'create'}),
        name='user-vehicles',
    ),
    path(
        'users/<int:user_pk>/vehicles/<int:pk>/',
        VehicleViewSet.as_view({'patch': 'partial_update'}),
        name='user-vehicle-detail',
    ),
]
