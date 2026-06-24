from django.contrib import admin
from .models import ViolationType, SanctionRule, Violation, Sanction


@admin.register(ViolationType)
class ViolationTypeAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'nivel', 'descripcion')
    list_filter = ('nivel',)


@admin.register(SanctionRule)
class SanctionRuleAdmin(admin.ModelAdmin):
    list_display = ('nivel_falta', 'numero_reincidencia', 'tipo_sancion', 'duracion_meses')
    list_filter = ('nivel_falta',)


@admin.register(Violation)
class ViolationAdmin(admin.ModelAdmin):
    list_display = ('user', 'tipo_falta', 'campus', 'fecha', 'estado')
    list_filter = ('estado', 'tipo_falta__nivel', 'campus')
    search_fields = ('user__codigo_institucional', 'vehicle__placa')
    readonly_fields = ('fecha',)


@admin.register(Sanction)
class SanctionAdmin(admin.ModelAdmin):
    list_display = ('user', 'tipo', 'inicio', 'fin', 'estado')
    list_filter = ('tipo', 'estado')
    search_fields = ('user__codigo_institucional',)
