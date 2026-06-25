from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ViolationViewSet, MyViolationsView

router = DefaultRouter()
router.register(r'violations', ViolationViewSet, basename='violation')

urlpatterns = [
    path('violations/my/', MyViolationsView.as_view(), name='my-violations'),
    path('', include(router.urls)),
]
