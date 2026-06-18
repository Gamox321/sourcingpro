from django.core.management.base import BaseCommand
from django.core.management import call_command


class Command(BaseCommand):
    help = "Configura la base de datos para la presentacion: roles, admin, seed completo"

    def handle(self, *args, **options):
        # 1. Crear roles
        self.stdout.write("Creando roles...")
        from apps.accounts.models import Role
        roles = ["rrhh", "jefatura", "ti", "prevencion", "finanzas", "logistica"]
        for r in roles:
            Role.objects.get_or_create(nombre=r)
        self.stdout.write("  7 roles creados")

        # 2. Crear admin (superuser)
        self.stdout.write("Creando administrador...")
        from apps.accounts.models import User, UserRole
        admin, created = User.objects.get_or_create(
            email="admin@sourcingpro.cl",
            defaults={
                "nombre": "Administrador",
                "contrasena_temporal": False,
                "is_superuser": True,
                "is_staff": True,
            },
        )
        if created:
            admin.set_password("Admin2024!")
            admin.save()
        if not admin.is_superuser:
            admin.is_superuser = True
            admin.is_staff = True
            admin.save()
        admin_role = Role.objects.get(nombre="administrador")
        UserRole.objects.get_or_create(usuario=admin, rol=admin_role)
        self.stdout.write("  admin@sourcingpro.cl / Admin2024!")

        # 3. Seed clients
        self.stdout.write("Creando clientes y CeCos...")
        call_command("seed_clients")

        # 4. Seed notifications
        self.stdout.write("Creando configuraciones de notificacion...")
        call_command("seed_notifications")

        # 5. Seed demo data
        self.stdout.write("Creando datos demo...")
        call_command("seed_demo")

        # 6. Summary
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("=" * 50))
        self.stdout.write(self.style.SUCCESS("  PRESENTACION LISTA"))
        self.stdout.write(self.style.SUCCESS("=" * 50))
        self.stdout.write("")
        self.stdout.write("  Credenciales de acceso:")
        self.stdout.write("    admin@sourcingpro.cl      / Admin2024!")
        self.stdout.write("    rrhh@sourcingpro.cl       / Demo2024!")
        self.stdout.write("    ti@sourcingpro.cl         / Demo2024!")
        self.stdout.write("    prevencion@sourcingpro.cl / Demo2024!")
        self.stdout.write("    finanzas@sourcingpro.cl   / Demo2024!")
        self.stdout.write("    logistica@sourcingpro.cl  / Demo2024!")
        self.stdout.write("    jefatura@sourcingpro.cl   / Demo2024!")
        self.stdout.write("")
