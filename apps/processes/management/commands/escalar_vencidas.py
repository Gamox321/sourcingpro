from django.core.management.base import BaseCommand
from apps.processes.services import verificar_vencidas


class Command(BaseCommand):
    help = "Marca como vencidas las tareas cuyo plazo límite ha expirado"

    def handle(self, *args, **options):
        verificar_vencidas()
        self.stdout.write(self.style.SUCCESS("Tareas vencidas actualizadas."))
