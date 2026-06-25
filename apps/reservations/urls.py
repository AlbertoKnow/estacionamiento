from django.urls import path
from .views import ReservationViewSet

urlpatterns = [
    path('reservations/', ReservationViewSet.as_view({'get': 'list', 'post': 'create'}), name='reservation-list'),
    path('reservations/<int:pk>/', ReservationViewSet.as_view({'get': 'retrieve', 'delete': 'destroy'}), name='reservation-detail'),
]
