from django.core.management.base import BaseCommand
from django.contrib.auth.hashers import make_password
from apps.accounts.models import User, Role, UserRole


class Command(BaseCommand):
    help = "Crea el superusuario administrador inicial"

    def add_arguments(self, parser):
        parser.add_argument("--email", default="admin@sourcingpro.cl")
        parser.add_argument("--nombre", default="Administrador")
        parser.add_argument("--password", default="Admin2024!")

    def handle(self, *args, **options):
        email = options["email"]
        nombre = options["nombre"]
        password = options["password"]

        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                "nombre": nombre,
                "contrasena_temporal": False,
                "is_staff": True,
                "is_superuser": True,
                "is_active": True,
                "password": make_password(password),
            },
        )

        if created:
            admin_role, _ = Role.objects.get_or_create(
                nombre=Role.RoleChoices.ADMINISTRADOR
            )
            UserRole.objects.get_or_create(usuario=user, rol=admin_role)
            self.stdout.write(
                self.style.SUCCESS(f"Administrador creado: {email} / {password}")
            )
        else:
            self.stdout.write(self.style.WARNING(f"El usuario {email} ya existe."))
