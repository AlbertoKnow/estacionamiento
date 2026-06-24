from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User, Vehicle


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('codigo_institucional', 'get_full_name', 'rol', 'estado', 'campus_asignado')
    list_filter = ('rol', 'estado', 'campus_asignado')
    search_fields = ('codigo_institucional', 'nombre', 'apellido', 'email')
    fieldsets = (
        (None, {'fields': ('codigo_institucional', 'email', 'password')}),
        ('Datos personales', {'fields': ('nombre', 'apellido')}),
        ('Rol y campus', {'fields': ('rol', 'campus_asignado', 'estado', 'suspension_hasta')}),
        ('Permisos', {'fields': ('is_active', 'is_staff', 'is_superuser')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('codigo_institucional', 'email', 'nombre', 'apellido', 'rol', 'password1', 'password2'),
        }),
    )
    ordering = ('codigo_institucional',)


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ('placa', 'user', 'tipo', 'activo')
    list_filter = ('tipo', 'activo')
    search_fields = ('placa', 'user__codigo_institucional')
