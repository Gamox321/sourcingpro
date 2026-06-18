from django.db import models


class Worker(models.Model):
    class EstadoChoices(models.TextChoices):
        EN_PROCESO = "en_proceso", "En proceso"
        ACTIVO = "activo", "Activo"
        EN_TRANSITO = "en_transito", "En tránsito"
        POR_EGRESAR = "por_egresar", "Por egresar"
        DESPEDIDO_EN_PROCESO = "despedido_en_proceso", "Despedido en proceso"
        DESVINCULADO = "desvinculado", "Desvinculado"
        ELIMINADO = "eliminado", "Eliminado"

    TRANSICIONES_VALIDAS = {
        "en_proceso": ["activo", "eliminado"],
        "activo": ["por_egresar", "despedido_en_proceso", "en_transito"],
        "en_transito": ["activo"],
        "por_egresar": ["activo", "desvinculado"],
        "despedido_en_proceso": ["desvinculado"],
        "desvinculado": [],
        "eliminado": [],
    }

    run = models.CharField(max_length=12, unique=True, verbose_name="RUN")
    nombre = models.CharField(max_length=100, verbose_name="Nombre completo")
    correo = models.EmailField(
        max_length=150, unique=True, verbose_name="Correo electrónico"
    )
    cargo = models.CharField(max_length=100, verbose_name="Cargo")
    fecha_ingreso_estimada = models.DateField(
        blank=True, null=True, verbose_name="Fecha ingreso estimada"
    )
    fecha_ingreso_efectiva = models.DateField(
        blank=True, null=True, verbose_name="Fecha ingreso efectiva"
    )
    estado = models.CharField(
        max_length=25,
        choices=EstadoChoices.choices,
        default=EstadoChoices.EN_PROCESO,
        verbose_name="Estado",
    )
    centro_costo_actual = models.ForeignKey(
        "clients.CostCenter",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="trabajadores",
        verbose_name="Centro de costo actual",
    )
    fecha_termino_contrato = models.DateField(
        blank=True, null=True, verbose_name="Fecha de término de contrato"
    )
    alerta_dias = models.PositiveIntegerField(
        default=30, verbose_name="Días de alerta para término"
    )
    cuenta_ti_email = models.EmailField(
        blank=True, null=True, verbose_name="Correo corporativo TI"
    )
    cuenta_ti_clave_inicial = models.CharField(
        max_length=100, blank=True, null=True, verbose_name="Clave inicial TI"
    )
    cuenta_ti_fecha_creacion = models.DateTimeField(
        blank=True, null=True, verbose_name="Fecha creación cuenta TI"
    )
    cuenta_ti_notas = models.TextField(
        blank=True, null=True, verbose_name="Notas de la cuenta TI"
    )

    class Meta:
        db_table = "trabajador"
        verbose_name = "Trabajador"
        verbose_name_plural = "Trabajadores"

    def __str__(self):
        return f"{self.nombre} ({self.run})"

    def puede_transicionar_a(self, nuevo_estado):
        return nuevo_estado in self.TRANSICIONES_VALIDAS.get(self.estado, [])

    def transiciones_permitidas(self):
        return self.TRANSICIONES_VALIDAS.get(self.estado, [])


class CostCenterHistory(models.Model):
    fecha_inicio = models.DateField(verbose_name="Fecha inicio")
    fecha_fin = models.DateField(blank=True, null=True, verbose_name="Fecha fin")
    trabajador = models.ForeignKey(
        Worker,
        on_delete=models.CASCADE,
        related_name="historial_ceco",
        verbose_name="Trabajador",
    )
    centro_costo = models.ForeignKey(
        "clients.CostCenter",
        on_delete=models.CASCADE,
        related_name="historial_trabajadores",
        verbose_name="Centro de costo",
    )
    proceso = models.ForeignKey(
        "processes.Process",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="+",
        verbose_name="Proceso origen",
    )

    class Meta:
        db_table = "historial_ceco"
        verbose_name = "Historial de CeCo"
        verbose_name_plural = "Historiales de CeCo"
        ordering = ["-fecha_inicio"]

    def __str__(self):
        return f"{self.trabajador} → {self.centro_costo} ({self.fecha_inicio})"
