from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction

from apps.accounts.models import User, Role, UserRole
from apps.clients.models import CostCenter
from apps.workers.models import Worker
from apps.inventory.models import AssetType, Asset, AssetAssignment
from apps.processes.services import (
    crear_proceso_contratacion, crear_proceso_cambio_ceco,
    crear_proceso_termino, crear_proceso_despido,
    completar_tarea,
)
from apps.notifications.services import notificar


class Command(BaseCommand):
    help = 'Crea datos de demostración para SourcingPro'

    def handle(self, *args, **options):
        admin = User.objects.filter(is_superuser=True).first()
        if not admin:
            self.stdout.write(self.style.ERROR('Ejecuta bootstrap_admin primero.'))
            return

        cecos = list(CostCenter.objects.filter(estado='activo'))
        if len(cecos) < 2:
            self.stdout.write(self.style.ERROR('Ejecuta seed_clients primero.'))
            return

        roles_map = {r.nombre: r for r in Role.objects.all()}

        usuarios = self._crear_usuarios(roles_map, admin)
        workers = self._crear_workers(cecos)
        self._crear_activos(cecos, workers, admin)
        self._crear_procesos(usuarios, workers, cecos)

        self._crear_notificaciones(usuarios, admin)

        self.stdout.write(self.style.SUCCESS('Datos demo creados exitosamente.'))

    def _crear_usuarios(self, roles_map, admin):
        usuarios_data = [
            ('rrhh@sourcingpro.cl', 'María González', 'rrhh'),
            ('jefatura@sourcingpro.cl', 'Carlos Muñoz', 'jefatura'),
            ('ti@sourcingpro.cl', 'Pedro Ramírez', 'ti'),
            ('prevencion@sourcingpro.cl', 'Ana Soto', 'prevencion'),
            ('finanzas@sourcingpro.cl', 'Luis Torres', 'finanzas'),
            ('logistica@sourcingpro.cl', 'Daniela Vega', 'logistica'),
        ]
        creados = {}
        for email, nombre, rol_nombre in usuarios_data:
            user, _ = User.objects.get_or_create(
                email=email,
                defaults={
                    'nombre': nombre,
                    'contrasena_temporal': False,
                },
            )
            user.set_password('Demo2024!')
            user.save()
            UserRole.objects.get_or_create(
                usuario=user,
                rol=roles_map[rol_nombre],
            )
            creados[rol_nombre] = user
        return creados

    def _crear_workers(self, cecos):
        workers_data = [
            ('12.345.678-9', 'Juan Pérez', 'juan.perez@minera.cl', 'Operador de Equipos', cecos[0]),
            ('9.876.543-2', 'María Soto', 'maria.soto@minera.cl', 'Ingeniera de Procesos', cecos[0]),
            ('15.234.567-8', 'Roberto Díaz', 'roberto.diaz@minera.cl', 'Mecánico', cecos[1]),
            ('11.222.333-4', 'Carmen Flores', 'carmen.flores@minera.cl', 'Supervisora', cecos[1]),
            ('8.765.432-1', 'Pablo Martínez', 'pablo.martinez@minera.cl', 'Geólogo', cecos[2]),
            ('13.579.246-8', 'Sofía Rojas', 'sofia.rojas@minera.cl', 'Analista SHEC', cecos[2]),
            ('14.258.369-7', 'Diego Vega', 'diego.vega@minera.cl', 'Operador', cecos[0]),
            ('10.111.222-3', 'Valentina Muñoz', 'valentina.munoz@minera.cl', 'Técnico Electricista', cecos[1]),
            ('16.171.819-0', 'Felipe Palma', 'felipe.palma@minera.cl', 'Administrativo', cecos[2]),
        ]
        workers = []
        for run, nombre, correo, cargo, ceco in workers_data:
            w, _ = Worker.objects.get_or_create(
                run=run,
                defaults={
                    'nombre': nombre,
                    'correo': correo,
                    'cargo': cargo,
                    'centro_costo_actual': ceco,
                    'estado': Worker.EstadoChoices.ACTIVO,
                    'fecha_ingreso_efectiva': timezone.now().date() - timedelta(days=90),
                },
            )
            workers.append(w)
        return workers

    def _crear_activos(self, cecos, workers, admin):
        tipos = {t.nombre: t for t in AssetType.objects.all()}
        if 'Equipo TI' in tipos:
            Asset.objects.get_or_create(
                codigo='TI-001',
                defaults={
                    'nombre': 'Notebook Dell Latitude',
                    'tipo': tipos['Equipo TI'],
                    'estado': 'asignado',
                },
            )
            Asset.objects.get_or_create(
                codigo='TI-002',
                defaults={
                    'nombre': 'Monitor Samsung 24"',
                    'tipo': tipos['Equipo TI'],
                    'estado': 'disponible',
                },
            )
        if 'EPP' in tipos:
            Asset.objects.get_or_create(
                codigo='EPP-001',
                defaults={
                    'nombre': 'Casco de Seguridad MSA',
                    'tipo': tipos['EPP'],
                    'estado': 'asignado',
                },
            )
            Asset.objects.get_or_create(
                codigo='EPP-002',
                defaults={
                    'nombre': 'Arnés de Seguridad',
                    'tipo': tipos['EPP'],
                    'estado': 'asignado',
                },
            )
            Asset.objects.get_or_create(
                codigo='EPP-003',
                defaults={
                    'nombre': 'Botas de Seguridad',
                    'tipo': tipos['EPP'],
                    'estado': 'disponible',
                },
            )

    def _crear_procesos(self, usuarios, workers, cecos):
        now = timezone.now()
        rrhh = usuarios.get('rrhh')

        p1 = crear_proceso_contratacion(rrhh, {
            'run': '20.123.456-7',
            'nombre': 'Andrés Castillo',
            'correo': 'andres.castillo@minera.cl',
            'cargo': 'Ayudante de Terreno',
            'centro_costo': cecos[0].pk,
            'fecha_ingreso_estimada': (now + timedelta(days=7)).date(),
            'motivo': 'Cubrir licencia médica',
        })
        for t in p1.tareas.all():
            completar_tarea(t)
        self.stdout.write(f'  Contratación #{p1.pk} completada (Andrés Castillo)')

        p2 = crear_proceso_contratacion(rrhh, {
            'run': '18.765.432-1',
            'nombre': 'Camila Reyes',
            'correo': 'camila.reyes@minera.cl',
            'cargo': 'Ingeniera en Prevención',
            'centro_costo': cecos[2].pk,
            'fecha_ingreso_estimada': (now + timedelta(days=14)).date(),
            'motivo': 'Nuevo puesto creado',
        })
        self.stdout.write(f'  Contratación #{p2.pk} en curso (Camila Reyes)')

        if len(workers) >= 3:
            p3 = crear_proceso_cambio_ceco(
                rrhh, workers[2].pk, cecos[0].pk,
                (now + timedelta(days=5)).date(),
                'Reasignación operativa',
            )
            self.stdout.write(f'  Cambio CeCo #{p3.pk} en curso ({workers[2].nombre})')

        if len(workers) >= 4:
            p4 = crear_proceso_termino(
                rrhh, workers[3].pk,
                (now + timedelta(days=30)).date(),
                'Término de contrato por periodo de prueba',
            )
            self.stdout.write(f'  Término #{p4.pk} en curso ({workers[3].nombre})')

        if len(workers) >= 5:
            p5 = crear_proceso_despido(
                rrhh, workers[4].pk,
                now.date(),
                'Incumplimiento de normas de seguridad',
                'Art. 160 N°5 — Incumplimiento grave de obligaciones',
            )
            self.stdout.write(f'  Despido #{p5.pk} en curso ({workers[4].nombre})')

    def _crear_notificaciones(self, usuarios, admin):
        for rol_nombre, user in usuarios.items():
            if rol_nombre in ('ti', 'logistica', 'prevencion', 'finanzas'):
                notificar(
                    usuario=user,
                    tipo_evento='tarea_cambio_estado',
                    titulo='Tienes tareas pendientes',
                    descripcion='Revisa el tablero kanban para ver tus tareas asignadas.',
                    enlace='/kanban/',
                )
