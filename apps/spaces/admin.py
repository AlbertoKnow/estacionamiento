from django.contrib import admin
from .models import Campus, ParkingLot, ParkingSpace


class ParkingLotInline(admin.TabularInline):
    model = ParkingLot
    extra = 1


class ParkingSpaceInline(admin.TabularInline):
    model = ParkingSpace
    extra = 1


@admin.register(Campus)
class CampusAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'ciudad', 'activo')
    list_filter = ('activo', 'ciudad')
    inlines = [ParkingLotInline]


@admin.register(ParkingLot)
class ParkingLotAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'campus', 'nivel')
    list_filter = ('campus',)
    inlines = [ParkingSpaceInline]


@admin.register(ParkingSpace)
class ParkingSpaceAdmin(admin.ModelAdmin):
    list_display = ('numero', 'lot', 'tipo', 'estado')
    list_filter = ('tipo', 'estado', 'lot__campus')
    search_fields = ('numero',)
