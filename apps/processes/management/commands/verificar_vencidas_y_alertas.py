from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import models as db_models
from datetime import timedelta

from apps.processes.models import Task, Process, TaskDeadlineConfig
from apps.workers.models import Worker
from apps.notifications.services import notificar
from apps.accounts.models import User, Role


class Command(BaseCommand):
    help = 'Verifica tareas vencidas, próximas a vencer y contratos por vencer'

    def handle(self, *args, **options):
        now = timezone.now()
        self.stdout.write(f'Ejecutando verificación: {now}')

        # 1. Verificar tareas vencidas
        self._verificar_tareas_vencidas(now)

        # 2. Verificar tareas próximas a vencer (2 días)
        self._verificar_tareas_proximas_vencer(now)

        # 3. Verificar contratos por vencer
        self._verificar_contratos_por_vencer(now)

        self.stdout.write(self.style.SUCCESS('Verificación completada.'))

    def _verificar_tareas_vencidas(self, now):
        """Marca tareas como vencidas y notifica al jefe de área"""
        tareas_vencidas = Task.objects.filter(
            plazo_limite__lt=now,
            estado__in=[Task.EstadoChoices.PENDIENTE, Task.EstadoChoices.EN_PROCESO],
            omitida=False,
            proceso__estado=Process.EstadoChoices.EN_CURSO,
        ).select_related('usuario_responsable', 'proceso__trabajador')

        for task in tareas_vencidas:
            task.estado = Task.EstadoChoices.VENCIDA
            task.save(update_fields=['estado'])

            # Notificar al responsable
            if task.usuario_responsable:
                notificar(
                    usuario=task.usuario_responsable,
                    tipo_evento='tarea_vencida',
                    titulo=f'TAREA VENCIDA: {task.get_tipo_display()}',
                    descripcion=f'Trabajador: {task.proceso.trabajador.nombre}. '
                                f'Proceso #{task.proceso.pk}. '
                                f'Plazo vencido: {task.plazo_limite.strftime("%d/%m/%Y")}',
                    proceso=task.proceso,
                    tarea=task,
                )

            # Notificar al jefe de área (escalamiento)
            self._notificar_al_jefe_de_area(task)

        self.stdout.write(f'  - {tareas_vencidas.count()} tareas marcadas como vencidas')

    def _verificar_tareas_proximas_vencer(self, now):
        """Notifica tareas que vencerán en 2 días"""
        prox_2_dias = now + timedelta(days=2)

        tareas_proximas = Task.objects.filter(
            plazo_limite__gte=now,
            plazo_limite__lte=prox_2_dias,
            estado__in=[Task.EstadoChoices.PENDIENTE, Task.EstadoChoices.EN_PROCESO],
            omitida=False,
            proceso__estado=Process.EstadoChoices.EN_CURSO,
        ).select_related('usuario_responsable', 'proceso__trabajador')

        for task in tareas_proximas:
            # Solo notificar si no se ha notificado antes (evitar duplicados)
            # Podríamos agregar un campo 'ultima_notificacion_proxima_vencimiento'
            if task.usuario_responsable:
                notificar(
                    usuario=task.usuario_responsable,
                    tipo_evento='tarea_proxima_vencer',
                    titulo=f'Tarea próxima a vencer: {task.get_tipo_display()}',
                    descripcion=f'Trabajador: {task.proceso.trabajador.nombre}. '
                                f'Vence: {task.plazo_limite.strftime("%d/%m/%Y %H:%M")}',
                    proceso=task.proceso,
                    tarea=task,
                )

        self.stdout.write(f'  - {tareas_proximas.count()} notificaciones de próximo vencimiento')

    def _verificar_contratos_por_vencer(self, now):
        """Detecta contratos por vencer según días de alerta configurados"""
        trabajadores_por_vencer = Worker.objects.filter(
            estado=Worker.EstadoChoices.ACTIVO,
            fecha_termino_contrato__isnull=False,
        )

        alertas_enviadas = 0
        for worker in trabajadores_por_vencer:
            dias_restantes = (worker.fecha_termino_contrato - now.date()).days
            dias_alerta = worker.alerta_dias or 30

            # Si faltan exactamente los días de alerta o menos (y no se ha iniciado proceso)
            if 0 <= dias_restantes <= dias_alerta:
                # Verificar que no haya un proceso de término activo
                proceso_termino_activo = Process.objects.filter(
                    trabajador=worker,
                    tipo=Process.TipoChoices.TERMINO,
                    estado=Process.EstadoChoices.EN_CURSO,
                ).exists()

                if not proceso_termino_activo:
                    # Notificar a RRHH
                    rrhh_users = User.objects.filter(
                        is_active=True, roles__nombre='rrhh'
                    ).distinct()
                    for rrhh_user in rrhh_users:
                        notificar(
                            usuario=rrhh_user,
                            tipo_evento='contrato_por_vencer',
                            titulo=f'CONTRATO POR VENCER: {worker.nombre}',
                            descripcion=f'RUN: {worker.run}. '
                                        f'Vence: {worker.fecha_termino_contrato.strftime("%d/%m/%Y")}. '
                                        f'Días restantes: {dias_restantes}. '
                                        f'Cargo: {worker.cargo}. '
                                        f'CeCo: {worker.centro_costo_actual}',
                        )
                    alertas_enviadas += 1

        self.stdout.write(f'  - {alertas_enviadas} alertas de contratos por vencer')

    def _notificar_al_jefe_de_area(self, task):
        """Notifica al jefe del área responsable sobre tarea vencida/escalada"""
        area = task.area_responsable
        if not area:
            return

        # Buscar jefe de área (usuarios con rol de jefatura y cecos a cargo)
        # O usuarios con rol específico del área
        jefes = User.objects.filter(
            is_active=True,
            roles__nombre__in=['administrador', 'jefatura', area]
        ).distinct()

        for jefe in jefes:
            notificar(
                usuario=jefe,
                tipo_evento='tarea_escalada',
                titulo=f'TAREA ESCALADA: {task.get_tipo_display()}',
                descripcion=f'Área: {task.area_responsable.upper()}. '
                            f'Responsable: {task.usuario_responsable.nombre if task.usuario_responsable else "Sin asignar"}. '
                            f'Trabajador: {task.proceso.trabajador.nombre}. '
                            f'Proceso #{task.proceso.pk}',
                proceso=task.proceso,
                tarea=task,
            )
