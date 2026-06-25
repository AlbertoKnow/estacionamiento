from django.urls import path
from .views import OccupancyReportView, ViolationsReportView, UsersReportView

urlpatterns = [
    path('reports/occupancy/', OccupancyReportView.as_view(), name='report-occupancy'),
    path('reports/violations/', ViolationsReportView.as_view(), name='report-violations'),
    path('reports/users/', UsersReportView.as_view(), name='report-users'),
]
