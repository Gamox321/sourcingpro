from django.core.management.base import BaseCommand
from apps.notifications.models import NotificationConfig
from apps.notifications.services import EVENTOS_NOTIFICABLES
from apps.accounts.models import User


class Command(BaseCommand):
    help = "Crea las configuraciones de notificación por defecto"

    def handle(self, *args, **options):
        admin = User.objects.filter(is_superuser=True).first()
        if not admin:
            self.stdout.write(
                self.style.ERROR(
                    "No hay administrador. Ejecuta bootstrap_admin primero."
                )
            )
            return

        canales = ["correo", "interno"]
        creadas = 0
        for evento in EVENTOS_NOTIFICABLES:
            for canal in canales:
                _, created = NotificationConfig.objects.get_or_create(
                    tipo_evento=evento,
                    canal=canal,
                    defaults={"activo": True, "usuario_modifico": admin},
                )
                if created:
                    creadas += 1

        self.stdout.write(
            self.style.SUCCESS(f"{creadas} configuraciones de notificación creadas.")
        )
