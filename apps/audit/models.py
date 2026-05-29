from django.db import models


class AuditLog(models.Model):
    class AccionChoices(models.TextChoices):
        CREACION = 'creacion', 'Creación'
        MODIFICACION = 'modificacion', 'Modificación'
        CAMBIO_ESTADO = 'cambio_estado', 'Cambio de estado'
        ELIMINACION_LOGICA = 'eliminacion_logica', 'Eliminación lógica'
        ESCALAMIENTO = 'escalamiento', 'Escalamiento'
        CIERRE = 'cierre', 'Cierre'

    tabla_afectada = models.CharField(max_length=50, verbose_name='Tabla afectada', db_index=True)
    accion = models.CharField(max_length=20, choices=AccionChoices.choices, verbose_name='Acción')
    descripcion = models.TextField(blank=True, null=True, verbose_name='Descripción')
    valor_anterior = models.JSONField(blank=True, null=True, verbose_name='Valor anterior')
    valor_nuevo = models.JSONField(blank=True, null=True, verbose_name='Valor nuevo')
    fecha_accion = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de acción', db_index=True)
    usuario = models.ForeignKey(
        'accounts.User', on_delete=models.CASCADE,
        verbose_name='Usuario'
    )
    id_entidad_afectada = models.IntegerField(verbose_name='ID de la entidad afectada')

    class Meta:
        db_table = 'bitacora'
        verbose_name = 'Auditoría'
        verbose_name_plural = 'Auditoría'
        ordering = ['-fecha_accion']
        indexes = [
            models.Index(fields=['tabla_afectada', 'id_entidad_afectada']),
        ]

    def __str__(self):
        return f'{self.get_accion_display()} en {self.tabla_afectada}#{self.id_entidad_afectada} ({self.fecha_accion.date()})'
