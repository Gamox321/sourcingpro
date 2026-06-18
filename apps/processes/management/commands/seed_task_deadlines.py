from django.core.management.base import BaseCommand
from apps.processes.models import Task, TaskDeadlineConfig


class Command(BaseCommand):
    help = "Crea configuración de plazos de tareas por defecto"

    def handle(self, *args, **options):
        defaults = [
            # (tipo_tarea, plazo_dias, plazo_escalamiento_dias, es_critica)
            (Task.TipoChoices.CREAR_CUENTA_TI, 3, 1, False),
            (Task.TipoChoices.EXAMENES_PREOCUPACIONALES, 5, 2, False),
            (Task.TipoChoices.EPP_INDUCCION, 3, 1, False),
            (Task.TipoChoices.EQUIPAMIENTO, 5, 2, False),
            (Task.TipoChoices.DEVOLUCION_ACTIVOS, 5, 2, False),
            (Task.TipoChoices.RECUPERACION_ACTIVOS, 3, 1, True),
            (Task.TipoChoices.PREPARAR_BLOQUEO_ACCESOS, 2, 1, True),
            (Task.TipoChoices.BLOQUEO_ACCESOS, 1, 0, True),
            (Task.TipoChoices.FINIQUITO_COORDINACION, 5, 2, False),
        ]

        created_count = 0
        updated_count = 0

        for tipo_tarea, plazo_dias, plazo_escalamiento, es_critica in defaults:
            config, created = TaskDeadlineConfig.objects.update_or_create(
                tipo_tarea=tipo_tarea,
                defaults={
                    "plazo_dias": plazo_dias,
                    "plazo_escalamiento_dias": plazo_escalamiento,
                    "es_critica": es_critica,
                },
            )
            if created:
                created_count += 1
                self.stdout.write(f"  Creado: {config}")
            else:
                updated_count += 1
                self.stdout.write(f"  Actualizado: {config}")

        self.stdout.write(
            self.style.SUCCESS(
                f"Configuración creada: {created_count}, Actualizada: {updated_count}"
            )
        )
