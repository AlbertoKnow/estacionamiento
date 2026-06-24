from django.contrib import admin
from .models import Campus, ParkingLot, ParkingSpace


@admin.register(Campus)
class CampusAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'ciudad', 'activo')
    list_filter = ('activo',)


@admin.register(ParkingLot)
class ParkingLotAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'campus', 'nivel')
    list_filter = ('campus',)


@admin.register(ParkingSpace)
class ParkingSpaceAdmin(admin.ModelAdmin):
    list_display = ('numero', 'lot', 'tipo', 'estado')
    list_filter = ('tipo', 'estado', 'lot__campus')
    search_fields = ('numero',)
