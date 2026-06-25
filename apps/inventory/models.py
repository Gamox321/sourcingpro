from django.core.exceptions import ValidationError
from django.db import models


class AssetType(models.Model):
    class EstadoChoices(models.TextChoices):
        ACTIVO = "activo", "Activo"
        INACTIVO = "inactivo", "Inactivo"

    nombre = models.CharField(max_length=100, unique=True, verbose_name="Nombre")
    descripcion = models.CharField(
        max_length=255, blank=True, null=True, verbose_name="Descripción"
    )
    estado = models.CharField(
        max_length=10,
        choices=EstadoChoices.choices,
        default=EstadoChoices.ACTIVO,
        verbose_name="Estado",
    )
    es_personalizado = models.BooleanField(
        default=False, verbose_name="Es personalizado"
    )
    es_ti = models.BooleanField(default=False, verbose_name="Visible en TI")
    es_prevencion = models.BooleanField(
        default=False, verbose_name="Visible en Prevención"
    )

    class Meta:
        db_table = "tipo_activo"
        verbose_name = "Tipo de Activo"
        verbose_name_plural = "Tipos de Activo"

    def __str__(self):
        return self.nombre


class Asset(models.Model):
    class EstadoChoices(models.TextChoices):
        DISPONIBLE = "disponible", "Disponible"
        ASIGNADO = "asignado", "Asignado"
        EN_REVISION = "en_revision", "En revisión"
        PENDIENTE_DEVOLUCION = "pendiente_devolucion", "Pendiente devolución"
        DADO_DE_BAJA = "dado_de_baja", "Dado de baja"

    TRANSICIONES_VALIDAS = {
        EstadoChoices.DISPONIBLE: [EstadoChoices.ASIGNADO, EstadoChoices.DADO_DE_BAJA],
        EstadoChoices.ASIGNADO: [
            EstadoChoices.PENDIENTE_DEVOLUCION,
            EstadoChoices.DADO_DE_BAJA,
        ],
        EstadoChoices.PENDIENTE_DEVOLUCION: [
            EstadoChoices.DISPONIBLE,
            EstadoChoices.EN_REVISION,
            EstadoChoices.DADO_DE_BAJA,
        ],
        EstadoChoices.EN_REVISION: [
            EstadoChoices.DISPONIBLE,
            EstadoChoices.DADO_DE_BAJA,
        ],
        EstadoChoices.DADO_DE_BAJA: [],
    }

    codigo = models.CharField(max_length=50, unique=True, verbose_name="Código")
    nombre = models.CharField(max_length=150, verbose_name="Nombre")
    marca = models.CharField(max_length=100, blank=True, verbose_name="Marca")
    modelo = models.CharField(max_length=100, blank=True, verbose_name="Modelo")
    numero_serie = models.CharField(
        max_length=100, blank=True, verbose_name="Número de serie"
    )
    estado = models.CharField(
        max_length=25,
        choices=EstadoChoices.choices,
        default=EstadoChoices.DISPONIBLE,
        verbose_name="Estado",
    )
    fecha_registro = models.DateField(
        auto_now_add=True, verbose_name="Fecha de registro"
    )
    motivo_baja = models.TextField(blank=True, null=True, verbose_name="Motivo de baja")
    tipo = models.ForeignKey(
        AssetType, on_delete=models.CASCADE, related_name="activos", verbose_name="Tipo"
    )

    class Meta:
        db_table = "activo"
        verbose_name = "Activo"
        verbose_name_plural = "Activos"

    def __str__(self):
        return f"{self.codigo} — {self.nombre}"

    def cambiar_estado(self, nuevo_estado):
        if nuevo_estado not in self.TRANSICIONES_VALIDAS.get(self.estado, []):
            raise ValidationError(
                f"Transición no válida de {self.get_estado_display()} a "
                f"{dict(self.EstadoChoices.choices).get(nuevo_estado, nuevo_estado)}."
            )
        if nuevo_estado == Asset.EstadoChoices.DADO_DE_BAJA and not self.motivo_baja:
            raise ValidationError("Debe indicar un motivo para dar de baja el activo.")
        self.estado = nuevo_estado
        self.save(update_fields=["estado"])

    def clean(self):
        if self.estado == Asset.EstadoChoices.DADO_DE_BAJA and not self.motivo_baja:
            raise ValidationError({"motivo_baja": "Debe indicar un motivo de baja."})


class AssetAssignment(models.Model):
    class EstadoDevolucionChoices(models.TextChoices):
        BUENO = "bueno", "Bueno"
        DANADO = "danado", "Dañado"
        CON_PERDIDA = "con_perdida", "Con pérdida"

    fecha_asignacion = models.DateTimeField(
        auto_now_add=True, verbose_name="Fecha de asignación"
    )
    fecha_devolucion = models.DateTimeField(
        blank=True, null=True, verbose_name="Fecha de devolución"
    )
    estado_devolucion = models.CharField(
        max_length=15,
        choices=EstadoDevolucionChoices.choices,
        blank=True,
        null=True,
        verbose_name="Estado de devolución",
    )
    notas_devolucion = models.TextField(blank=True, null=True, verbose_name="Notas de devolución")
    foto_evidencia = models.FileField(
        upload_to="evidencias/activos/",
        blank=True,
        null=True,
        verbose_name="Foto/Archivo evidencia",
    )
    foto_evidencia_url = models.CharField(
        max_length=500,
        blank=True,
        null=True,
        verbose_name="Foto evidencia (URL alternativa)",
        help_text="URL externa como alternativa a la subida de archivo. "
        "Ambos campos son mutuamente excluyentes en la práctica "
        "(la vista de logistica asigna uno y limpia el otro).",
    )
    activo = models.ForeignKey(
        Asset,
        on_delete=models.CASCADE,
        related_name="asignaciones",
        verbose_name="Activo",
    )
    trabajador = models.ForeignKey(
        "workers.Worker",
        on_delete=models.CASCADE,
        related_name="activos_asignados",
        verbose_name="Trabajador",
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
        db_table = "asignacion_activo"
        verbose_name = "Asignación de Activo"
        verbose_name_plural = "Asignaciones de Activos"
        ordering = ["-fecha_asignacion"]

    def __str__(self):
        return f"{self.activo.codigo} → {self.trabajador.nombre} ({self.fecha_asignacion.date()})"

    def clean(self):
        if (self.fecha_devolucion is None) != (self.estado_devolucion is None):
            raise ValidationError(
                "fecha_devolucion y estado_devolucion deben indicarse juntos o ninguno."
            )
        if (
            self.fecha_devolucion
            and self.fecha_asignacion
            and self.fecha_devolucion < self.fecha_asignacion
        ):
            raise ValidationError(
                "La fecha de devolución debe ser posterior a la fecha de asignación."
            )

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
