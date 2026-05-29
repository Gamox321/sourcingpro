from django.contrib import admin
from .models import Worker, CostCenterHistory


class CostCenterHistoryInline(admin.TabularInline):
    model = CostCenterHistory
    extra = 0
    readonly_fields = ('fecha_inicio', 'fecha_fin', 'proceso')
    can_delete = False


@admin.register(Worker)
class WorkerAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'run', 'estado', 'cargo', 'centro_costo_actual')
    list_filter = ('estado',)
    search_fields = ('nombre', 'run', 'correo')
    list_select_related = ('centro_costo_actual',)
    inlines = (CostCenterHistoryInline,)


@admin.register(CostCenterHistory)
class CostCenterHistoryAdmin(admin.ModelAdmin):
    list_display = ('trabajador', 'centro_costo', 'fecha_inicio', 'fecha_fin', 'proceso')
    list_filter = ('centro_costo',)
    search_fields = ('trabajador__nombre', 'trabajador__run')
    list_select_related = ('trabajador', 'centro_costo', 'proceso')
