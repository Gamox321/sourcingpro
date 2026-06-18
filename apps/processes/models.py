from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class Process(models.Model):
    class TipoChoices(models.TextChoices):
        CONTRATACION = "contratacion", "Contratación"
        CAMBIO_CECO = "cambio_ceco", "Cambio de Centro de Costo"
        TERMINO = "termino", "Término de Contrato"
        DESPIDO = "despido", "Despido"
        ASIGNACION_ACTIVOS = "asignacion_activos", "Asignación de Activos TI"
        ASIGNACION_EPP = "asignacion_epp", "Asignación de EPP"

    class EstadoChoices(models.TextChoices):
        EN_CURSO = "en_curso", "En curso"
        COMPLETADO = "completado", "Completado"
        CANCELADO = "cancelado", "Cancelado"

    tipo = models.CharField(
        max_length=20, choices=TipoChoices.choices, verbose_name="Tipo"
    )
    estado = models.CharField(
        max_length=12,
        choices=EstadoChoices.choices,
        default=EstadoChoices.EN_CURSO,
        verbose_name="Estado",
    )
    fecha_inicio = models.DateTimeField(
        auto_now_add=True, verbose_name="Fecha de inicio"
    )
    fecha_cierre = models.DateTimeField(
        blank=True, null=True, verbose_name="Fecha de cierre"
    )
    motivo = models.TextField(blank=True, null=True, verbose_name="Motivo")
    causal_legal = models.TextField(blank=True, null=True, verbose_name="Causal legal")
    trabajador = models.ForeignKey(
        "workers.Worker",
        on_delete=models.CASCADE,
        related_name="procesos",
        verbose_name="Trabajador",
    )
    usuario_inicio = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="procesos_iniciados",
        verbose_name="Iniciado por",
    )
    ceco_origen = models.ForeignKey(
        "clients.CostCenter",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="procesos_origen",
        verbose_name="CeCo origen",
    )
    ceco_destino = models.ForeignKey(
        "clients.CostCenter",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="procesos_destino",
        verbose_name="CeCo destino",
    )
    requiere_confirmacion_rrhh = models.BooleanField(default=False)

    class Meta:
        db_table = "proceso"
        verbose_name = "Proceso"
        verbose_name_plural = "Procesos"
        ordering = ["-fecha_inicio"]

    def __str__(self):
        return f"{self.get_tipo_display()} #{self.pk} — {self.trabajador.nombre}"

    def clean(self):
        if self.causal_legal and self.tipo != self.TipoChoices.DESPIDO:
            raise ValidationError(
                {"causal_legal": "Solo aplica en procesos de despido."}
            )
        if self.ceco_destino and self.tipo != self.TipoChoices.CAMBIO_CECO:
            raise ValidationError(
                {"ceco_destino": "Solo aplica en cambios de centro de costo."}
            )
        if (
            self.fecha_cierre
            and self.fecha_inicio
            and self.fecha_cierre < self.fecha_inicio
        ):
            raise ValidationError(
                "La fecha de cierre debe ser posterior a la fecha de inicio."
            )

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)


class Task(models.Model):
    class TipoChoices(models.TextChoices):
        CREAR_CUENTA_TI = "crear_cuenta_ti", "Creación de cuenta TI"
        EXAMENES_PREOCUPACIONALES = (
            "examenes_preocupacionales",
            "Exámenes preocupacionales",
        )
        EPP_INDUCCION = "epp_induccion", "EPP e Inducción"
        EQUIPAMIENTO = "equipamiento", "Equipamiento"
        DEVOLUCION_ACTIVOS = "devolucion_activos", "Devolución de activos"
        RECUPERACION_ACTIVOS = "recuperacion_activos", "Recuperación de activos"
        PREPARAR_BLOQUEO_ACCESOS = (
            "preparar_bloqueo_accesos",
            "Preparar bloqueo de accesos",
        )
        BLOQUEO_ACCESOS = "bloqueo_accesos", "Bloqueo de accesos"
        FINIQUITO_COORDINACION = "finiquito_coordinacion", "Coordinación de finiquito"
        ASIGNAR_EQUIPO_TI = "asignar_equipo_ti", "Asignación de Equipo TI"
        DEVOLUCION_EPP = "devolucion_epp", "Devolución de EPP"
        ASIGNAR_EPP = "asignar_epp", "Asignación de EPP"

    TIPO_AREA_MAP = {
        TipoChoices.CREAR_CUENTA_TI: "ti",
        TipoChoices.EXAMENES_PREOCUPACIONALES: "prevencion",
        TipoChoices.EPP_INDUCCION: "prevencion",
        TipoChoices.EQUIPAMIENTO: "logistica",
        TipoChoices.DEVOLUCION_ACTIVOS: "logistica",
        TipoChoices.RECUPERACION_ACTIVOS: "logistica",
        TipoChoices.PREPARAR_BLOQUEO_ACCESOS: "ti",
        TipoChoices.BLOQUEO_ACCESOS: "ti",
        TipoChoices.FINIQUITO_COORDINACION: "finanzas",
        TipoChoices.ASIGNAR_EQUIPO_TI: "ti",
        TipoChoices.DEVOLUCION_EPP: "prevencion",
        TipoChoices.ASIGNAR_EPP: "prevencion",
    }

    class EstadoChoices(models.TextChoices):
        PENDIENTE = "pendiente", "Pendiente"
        EN_PROCESO = "en_proceso", "En proceso"
        COMPLETADA = "completada", "Completada"
        VENCIDA = "vencida", "Vencida"
        ESCALADA = "escalada", "Escalada"
        GESTIONADO_EXTERNO = "gestionado_externo", "Gestionado externo"

    class UrgenciaChoices(models.TextChoices):
        NORMAL = "normal", "Normal"
        CRITICA = "critica", "Crítica"

    tipo = models.CharField(
        max_length=30, choices=TipoChoices.choices, verbose_name="Tipo"
    )
    estado = models.CharField(
        max_length=20,
        choices=EstadoChoices.choices,
        default=EstadoChoices.PENDIENTE,
        verbose_name="Estado",
    )
    urgencia = models.CharField(
        max_length=10,
        choices=UrgenciaChoices.choices,
        default=UrgenciaChoices.NORMAL,
        verbose_name="Urgencia",
    )
    plazo_limite = models.DateTimeField(
        blank=True, null=True, verbose_name="Plazo límite"
    )
    fecha_completado = models.DateTimeField(
        blank=True, null=True, verbose_name="Fecha completado"
    )
    descripcion = models.TextField(blank=True, null=True, verbose_name="Descripción")
    orden = models.PositiveIntegerField(default=0, db_index=True, verbose_name="Orden")
    omitida = models.BooleanField(default=False, verbose_name="Omitida")
    motivo_omision = models.CharField(
        max_length=255, blank=True, null=True, verbose_name="Motivo de omisión"
    )
    proceso = models.ForeignKey(
        Process, on_delete=models.CASCADE, related_name="tareas", verbose_name="Proceso"
    )
    usuario_responsable = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="tareas_asignadas",
        verbose_name="Responsable",
    )

    class Meta:
        db_table = "tarea"
        verbose_name = "Tarea"
        verbose_name_plural = "Tareas"
        ordering = ["orden", "-urgencia", "plazo_limite"]

    def __str__(self):
        return f"{self.get_tipo_display()} — {self.proceso}"

    @property
    def area_responsable(self):
        return self.TIPO_AREA_MAP.get(self.tipo, "")

    @property
    def dias_restantes(self):
        if not self.plazo_limite:
            return None
        return (self.plazo_limite.date() - timezone.now().date()).days

    def tareas_anteriores(self):
        return (
            self.proceso.tareas.filter(orden__lt=self.orden)
            .exclude(
                estado__in=[
                    self.EstadoChoices.COMPLETADA,
                    self.EstadoChoices.GESTIONADO_EXTERNO,
                ]
            )
            .exclude(omitida=True)
        )

    def clean(self):
        if self.motivo_omision and not self.omitida:
            raise ValidationError(
                {"motivo_omision": "Solo aplica cuando la tarea está omitida."}
            )
        if self.fecha_completado and self.estado not in (
            self.EstadoChoices.COMPLETADA,
            self.EstadoChoices.GESTIONADO_EXTERNO,
        ):
            raise ValidationError(
                {
                    "fecha_completado": "Solo aplica cuando el estado es Completada o Gestionado externo."
                }
            )

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)


class TaskDeadlineConfig(models.Model):
    class Meta:
        db_table = "config_plazo_tarea"
        verbose_name = "Configuración de Plazo de Tarea"
        verbose_name_plural = "Configuraciones de Plazos de Tareas"
        unique_together = ("tipo_tarea",)

    tipo_tarea = models.CharField(
        max_length=30,
        choices=Task.TipoChoices.choices,
        unique=True,
        verbose_name="Tipo de tarea",
    )
    plazo_dias = models.PositiveIntegerField(default=5, verbose_name="Plazo (días)")
    plazo_escalamiento_dias = models.PositiveIntegerField(
        default=2, verbose_name="Plazo de escalamiento (días)"
    )
    es_critica = models.BooleanField(default=False, verbose_name="Es crítica")

    def __str__(self):
        return f"{dict(Task.TipoChoices.choices).get(self.tipo_tarea, self.tipo_tarea)} — {self.plazo_dias} días"

    def clean(self):
        if self.plazo_escalamiento_dias >= self.plazo_dias:
            raise ValidationError(
                {
                    "plazo_escalamiento_dias": "El plazo de escalamiento debe ser menor al plazo total."
                }
            )

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
