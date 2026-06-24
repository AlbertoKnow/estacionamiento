from django.contrib import admin
from .models import AccessRecord, UsedQRToken


@admin.register(AccessRecord)
class AccessRecordAdmin(admin.ModelAdmin):
    list_display = ('user', 'campus', 'space', 'entrada_at', 'salida_at', 'estado')
    list_filter = ('estado', 'campus')
    search_fields = ('user__codigo_institucional', 'vehicle__placa')
    readonly_fields = ('entrada_at',)


@admin.register(UsedQRToken)
class UsedQRTokenAdmin(admin.ModelAdmin):
    list_display = ('jti', 'user_id', 'used_at')
    readonly_fields = ('used_at',)
