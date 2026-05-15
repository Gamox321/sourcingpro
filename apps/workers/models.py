from django.db import models


class Worker(models.Model):
    class EstadoChoices(models.TextChoices):
        EN_PROCESO = 'en_proceso', 'En proceso'
        ACTIVO = 'activo', 'Activo'
        EN_TRANSITO = 'en_transito', 'En tránsito'
        POR_EGRESAR = 'por_egresar', 'Por egresar'
        DESPEDIDO_EN_PROCESO = 'despedido_en_proceso', 'Despedido en proceso'
        DESVINCULADO = 'desvinculado', 'Desvinculado'
        ELIMINADO = 'eliminado', 'Eliminado'

    run = models.CharField(max_length=12, unique=True, verbose_name='RUN')
    nombre = models.CharField(max_length=100, verbose_name='Nombre completo')
    correo = models.EmailField(max_length=150, unique=True, verbose_name='Correo electrónico')
    cargo = models.CharField(max_length=100, verbose_name='Cargo')
    fecha_ingreso_estimada = models.DateField(blank=True, null=True, verbose_name='Fecha ingreso estimada')
    fecha_ingreso_efectiva = models.DateField(blank=True, null=True, verbose_name='Fecha ingreso efectiva')
    estado = models.CharField(
        max_length=25, choices=EstadoChoices.choices,
        default=EstadoChoices.EN_PROCESO, verbose_name='Estado'
    )
    centro_costo_actual = models.ForeignKey(
        'clients.CostCenter', on_delete=models.SET_NULL,
        blank=True, null=True, related_name='trabajadores',
        verbose_name='Centro de costo actual'
    )

    class Meta:
        db_table = 'trabajador'
        verbose_name = 'Trabajador'
        verbose_name_plural = 'Trabajadores'

    def __str__(self):
        return f'{self.nombre} ({self.run})'


class CostCenterHistory(models.Model):
    fecha_inicio = models.DateField(verbose_name='Fecha inicio')
    fecha_fin = models.DateField(blank=True, null=True, verbose_name='Fecha fin')
    trabajador = models.ForeignKey(
        Worker, on_delete=models.CASCADE,
        related_name='historial_ceco', verbose_name='Trabajador'
    )
    centro_costo = models.ForeignKey(
        'clients.CostCenter', on_delete=models.CASCADE,
        related_name='historial_trabajadores', verbose_name='Centro de costo'
    )
    proceso = models.ForeignKey(
        'processes.Process', on_delete=models.SET_NULL,
        blank=True, null=True, related_name='+',
        verbose_name='Proceso origen'
    )

    class Meta:
        db_table = 'historial_ceco'
        verbose_name = 'Historial de CeCo'
        verbose_name_plural = 'Historiales de CeCo'
        ordering = ['-fecha_inicio']

    def __str__(self):
        return f'{self.trabajador} → {self.centro_costo} ({self.fecha_inicio})'
