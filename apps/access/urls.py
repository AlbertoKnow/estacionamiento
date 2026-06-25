from django.urls import path
from .views import (
    GenerateEntryQRView,
    EntryView,
    ExitView,
    SyncOfflineExitsView,
    AccessHistoryView,
)

urlpatterns = [
    path('access/qr/entry/', GenerateEntryQRView.as_view(), name='access-qr-entry'),
    path('access/entry/', EntryView.as_view(), name='access-entry'),
    path('access/exit/', ExitView.as_view(), name='access-exit'),
    path('access/exit/sync/', SyncOfflineExitsView.as_view(), name='access-exit-sync'),
    path('access/history/', AccessHistoryView.as_view(), name='access-history'),
]
