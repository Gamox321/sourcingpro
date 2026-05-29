from django.contrib import admin
from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('fecha_accion', 'usuario', 'tabla_afectada', 'id_entidad_afectada', 'get_accion_display')
    list_filter = ('accion', 'tabla_afectada')
    search_fields = ('descripcion',)
    date_hierarchy = 'fecha_accion'
    readonly_fields = ('tabla_afectada', 'accion', 'descripcion', 'valor_anterior', 'valor_nuevo', 'fecha_accion', 'usuario', 'id_entidad_afectada')

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
