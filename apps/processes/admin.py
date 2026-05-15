from django.contrib import admin
from .models import Process, Task


class TaskInline(admin.TabularInline):
    model = Task
    extra = 0
    readonly_fields = ('tipo', 'estado', 'urgencia', 'usuario_responsable')
    can_delete = False


@admin.register(Process)
class ProcessAdmin(admin.ModelAdmin):
    list_display = ('pk', 'get_tipo_display', 'get_estado_display', 'trabajador', 'usuario_inicio', 'fecha_inicio')
    list_filter = ('tipo', 'estado')
    search_fields = ('trabajador__nombre', 'trabajador__run')
    inlines = (TaskInline,)


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('get_tipo_display', 'get_estado_display', 'urgencia', 'proceso', 'usuario_responsable', 'plazo_limite')
    list_filter = ('estado', 'urgencia', 'tipo')
    search_fields = ('proceso__trabajador__nombre',)
