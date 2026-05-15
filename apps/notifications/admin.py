from django.contrib import admin
from .models import Notification, NotificationConfig


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('fecha_envio', 'usuario_destinatario', 'tipo_evento', 'get_canal_display', 'get_estado_display')
    list_filter = ('estado', 'canal', 'tipo_evento')
    search_fields = ('contenido', 'usuario_destinatario__nombre')
    date_hierarchy = 'fecha_envio'
    readonly_fields = ('fecha_envio',)


@admin.register(NotificationConfig)
class NotificationConfigAdmin(admin.ModelAdmin):
    list_display = ('tipo_evento', 'get_canal_display', 'activo', 'ultima_modificacion')
    list_filter = ('activo', 'canal')
    search_fields = ('tipo_evento',)
