from django.db import models


class Client(models.Model):
    nombre = models.CharField(max_length=100, unique=True, verbose_name="Nombre")
    descripcion = models.CharField(
        max_length=255, blank=True, null=True, verbose_name="Descripción"
    )

    class Meta:
        db_table = "cliente"
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"

    def __str__(self):
        return self.nombre


class CostCenter(models.Model):
    class EstadoChoices(models.TextChoices):
        ACTIVO = "activo", "Activo"
        INACTIVO = "inactivo", "Inactivo"

    nombre = models.CharField(max_length=100, verbose_name="Nombre")
    codigo = models.CharField(max_length=20, unique=True, verbose_name="Código")
    estado = models.CharField(
        max_length=10,
        choices=EstadoChoices.choices,
        default=EstadoChoices.ACTIVO,
        verbose_name="Estado",
    )
    cliente = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        related_name="centros_costo",
        verbose_name="Cliente",
    )
    jefatura = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="cecos_a_cargo",
        verbose_name="Jefatura responsable",
    )

    class Meta:
        db_table = "centro_costo"
        verbose_name = "Centro de Costo"
        verbose_name_plural = "Centros de Costo"

    def __str__(self):
        return f"{self.nombre} ({self.codigo})"
