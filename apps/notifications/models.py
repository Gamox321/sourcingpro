from django.db import models


class Notification(models.Model):
    class CanalChoices(models.TextChoices):
        CORREO = 'correo', 'Correo electrónico'
        INTERNO = 'interno', 'Interno'

    class EstadoChoices(models.TextChoices):
        PENDIENTE = 'pendiente', 'Pendiente'
        ENVIADA = 'enviada', 'Enviada'
        LEIDA = 'leida', 'Leída'
        ELIMINADA = 'eliminada', 'Eliminada'

    tipo_evento = models.CharField(max_length=100, verbose_name='Tipo de evento', db_index=True)
    contenido = models.TextField(verbose_name='Contenido')
    canal = models.CharField(max_length=10, choices=CanalChoices.choices, verbose_name='Canal')
    estado = models.CharField(
        max_length=10, choices=EstadoChoices.choices,
        default=EstadoChoices.PENDIENTE, verbose_name='Estado'
    )
    fecha_envio = models.DateTimeField(blank=True, null=True, verbose_name='Fecha de envío')
    usuario_destinatario = models.ForeignKey(
        'accounts.User', on_delete=models.CASCADE,
        related_name='notificaciones', verbose_name='Destinatario'
    )
    proceso = models.ForeignKey(
        'processes.Process', on_delete=models.SET_NULL,
        blank=True, null=True, related_name='+', verbose_name='Proceso'
    )
    tarea = models.ForeignKey(
        'processes.Task', on_delete=models.SET_NULL,
        blank=True, null=True, related_name='+', verbose_name='Tarea'
    )

    class Meta:
        db_table = 'notificacion'
        verbose_name = 'Notificación'
        verbose_name_plural = 'Notificaciones'
        ordering = ['-fecha_envio', '-pk']

    def __str__(self):
        return f'[{self.get_canal_display()}] {self.tipo_evento} → {self.usuario_destinatario.nombre}'


class NotificationConfig(models.Model):
    class CanalChoices(models.TextChoices):
        CORREO = 'correo', 'Correo electrónico'
        INTERNO = 'interno', 'Interno'

    tipo_evento = models.CharField(max_length=100, verbose_name='Tipo de evento')
    canal = models.CharField(max_length=10, choices=CanalChoices.choices, verbose_name='Canal')
    activo = models.BooleanField(default=True, verbose_name='Activo')
    ultima_modificacion = models.DateTimeField(auto_now=True, verbose_name='Última modificación')
    usuario_modifico = models.ForeignKey(
        'accounts.User', on_delete=models.CASCADE,
        verbose_name='Modificado por'
    )

    class Meta:
        db_table = 'config_notificacion'
        verbose_name = 'Configuración de notificación'
        verbose_name_plural = 'Configuraciones de notificaciones'
        unique_together = ('tipo_evento', 'canal')

    def __str__(self):
        return f'{self.tipo_evento} [{self.get_canal_display()}] {"✓" if self.activo else "✗"}'
