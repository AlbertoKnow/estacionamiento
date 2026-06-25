from django.urls import path
from .views import CampusViewSet, ParkingLotViewSet, ParkingSpaceViewSet, CampusOccupancyView

campus_list = CampusViewSet.as_view({'get': 'list', 'post': 'create'})
campus_detail = CampusViewSet.as_view({'get': 'retrieve', 'patch': 'partial_update'})
lot_list = ParkingLotViewSet.as_view({'get': 'list'})
lot_detail = ParkingLotViewSet.as_view({'get': 'retrieve'})
space_list = ParkingSpaceViewSet.as_view({'get': 'list', 'post': 'create'})
space_detail = ParkingSpaceViewSet.as_view({'get': 'retrieve', 'patch': 'partial_update'})

urlpatterns = [
    path('campus/', campus_list, name='campus-list'),
    path('campus/<int:pk>/', campus_detail, name='campus-detail'),
    path('campus/<int:campus_pk>/lots/', lot_list, name='lot-list'),
    path('campus/<int:campus_pk>/lots/<int:pk>/', lot_detail, name='lot-detail'),
    path('campus/<int:campus_pk>/lots/<int:lot_pk>/spaces/', space_list, name='space-list'),
    path('campus/<int:campus_pk>/lots/<int:lot_pk>/spaces/<int:pk>/', space_detail, name='space-detail'),
    path('campus/<int:campus_pk>/occupancy/', CampusOccupancyView.as_view(), name='campus-occupancy'),
]
