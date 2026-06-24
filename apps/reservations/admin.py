from django.contrib import admin
from .models import Reservation


@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ('space', 'reservado_por', 'beneficiario', 'inicio', 'fin', 'estado')
    list_filter = ('estado', 'campus')
    search_fields = ('reservado_por__codigo_institucional', 'space__numero')
    readonly_fields = ('created_at',)
