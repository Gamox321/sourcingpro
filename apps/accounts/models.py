from django.contrib.auth.models import AbstractUser
from django.db import models


class Role(models.Model):
    class RoleChoices(models.TextChoices):
        ADMINISTRADOR = 'administrador', 'Administrador'
        RRHH = 'rrhh', 'RRHH'
        JEFATURA = 'jefatura', 'Jefatura'
        TI = 'ti', 'TI'
        PREVENCION = 'prevencion', 'Prevención de Riesgos'
        FINANZAS = 'finanzas', 'Finanzas'
        LOGISTICA = 'logistica', 'Logística'

    nombre = models.CharField(
        max_length=20, choices=RoleChoices.choices,
        unique=True, verbose_name='Nombre del rol'
    )
    descripcion = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        db_table = 'rol'
        verbose_name = 'Rol'
        verbose_name_plural = 'Roles'

    def __str__(self):
        return self.get_nombre_display()


class User(AbstractUser):
    username = None
    first_name = None
    last_name = None

    email = models.EmailField(
        unique=True, max_length=150, verbose_name='Correo electrónico'
    )
    nombre = models.CharField(max_length=100, verbose_name='Nombre completo')
    contrasena_temporal = models.BooleanField(
        default=True, verbose_name='Contraseña temporal'
    )
    intentos_fallidos = models.IntegerField(
        default=0, verbose_name='Intentos fallidos'
    )
    fecha_creacion = models.DateTimeField(
        auto_now_add=True, verbose_name='Fecha de creación'
    )
    roles = models.ManyToManyField(
        Role, through='UserRole', related_name='usuarios'
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['nombre']

    class Meta:
        db_table = 'usuario'
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'

    def __str__(self):
        return self.nombre

    @property
    def es_administrador(self):
        return self.roles.filter(nombre=Role.RoleChoices.ADMINISTRADOR).exists()


class UserRole(models.Model):
    usuario = models.ForeignKey(
        User, on_delete=models.CASCADE, verbose_name='Usuario'
    )
    rol = models.ForeignKey(
        Role, on_delete=models.CASCADE, verbose_name='Rol'
    )
    fecha_asignacion = models.DateTimeField(
        auto_now_add=True, verbose_name='Fecha de asignación'
    )

    class Meta:
        db_table = 'usuario_rol'
        verbose_name = 'Asignación de rol'
        verbose_name_plural = 'Asignaciones de roles'
        unique_together = ('usuario', 'rol')

    def __str__(self):
        return f'{self.usuario.nombre} — {self.rol.get_nombre_display()}'
