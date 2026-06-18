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
    crear_proceso_asignacion_activos,
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

        # Asignar centros de costo a la jefatura para que pueda ver trabajadores
        jefatura_user = usuarios.get('jefatura')
        if jefatura_user:
            for ceco in cecos:
                ceco.jefatura = jefatura_user
                ceco.save()

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
        self._seed_asset_types()
        tipos = {t.nombre: t for t in AssetType.objects.all()}

        ti_types = ['Notebook', 'Monitor', 'Computador', 'Periférico', 'Teléfono', 'Impresora']
        epp_types = ['Casco', 'Guantes', 'Chaleco reflectante', 'Zapatos seguridad',
                     'Lentes seguridad', 'Arnés', 'Protector auditivo', 'Respirador', 'Ropa trabajo']

        ti_models = ['Dell Latitude', 'HP EliteBook', 'Lenovo ThinkPad', 'MacBook Pro',
                     'Samsung 24"', 'LG 27"', 'Dell 27"', 'HP 22"',
                     'OptiPlex 7080', 'EliteDesk 800', 'ThinkCentre M90',
                     'Teclado Logitech', 'Mouse Logitech', 'Webcam HD', 'Audífonos Jabra',
                     'iPhone 14', 'Samsung Galaxy', 'iPhone 15',
                     'HP LaserJet', 'Brother MFC', 'Epson EcoTank']

        epp_models = ['Casco MSA V-Gard', 'Casco 3M H-700', 'Casco Kask Zenith',
                      'Guante nitrilo', 'Guante cuero', 'Guante anticorte',
                      'Chaleco amarillo', 'Chaleco naranja', 'Chaleco verde',
                      'Bota seguridad 3M', 'Zapato dieléctrico', 'Bota punta composite',
                      'Lente 3M claro', 'Lente oscuro', 'Goggle antiempañante',
                      'Arnés cuerpo completo', 'Arnés posicionamiento',
                      'Orejera 3M Peltor', 'Tapón reutilizable',
                      'Respirador N95', 'Media cara 3M',
                      'Overol azul', 'Overol naranja', 'Chaqueta trabajo']

        total_ti = 0
        for i in range(1, 34):
            tipo_name = ti_types[i % len(ti_types)]
            model = ti_models[(i - 1) % len(ti_models)]
            Asset.objects.get_or_create(
                codigo='TI-{:03d}'.format(i),
                defaults={
                    'nombre': '{} {}'.format(tipo_name, model),
                    'tipo': tipos[tipo_name],
                    'estado': 'disponible',
                },
            )
            total_ti += 1

        total_epp = 0
        for i in range(1, 34):
            tipo_name = epp_types[i % len(epp_types)]
            model = epp_models[(i - 1) % len(epp_models)]
            Asset.objects.get_or_create(
                codigo='EPP-{:03d}'.format(i),
                defaults={
                    'nombre': '{} {}'.format(tipo_name, model),
                    'tipo': tipos[tipo_name],
                    'estado': 'disponible',
                },
            )
            total_epp += 1

        self.stdout.write('  {} activos TI creados'.format(total_ti))
        self.stdout.write('  {} activos EPP creados'.format(total_epp))

    def _seed_asset_types(self):
        tipos_ti = [
            ('Computador', 'Computadores de escritorio y estaciones de trabajo'),
            ('Tablet', 'Tablets y dispositivos móviles táctiles'),
            ('Notebook', 'Laptops, notebooks y ultrabooks'),
            ('Monitor', 'Monitores y pantallas'),
            ('Teléfono', 'Teléfonos fijos y smartphones corporativos'),
            ('Impresora', 'Impresoras, escáneres y multifuncionales'),
            ('Periférico', 'Teclados, mouse, audífonos, webcams y otros periféricos'),
            ('Equipos TI', 'Equipos tecnológicos generales (legado)'),
        ]
        tipos_epp = [
            ('Casco', 'Cascos de seguridad industrial'),
            ('Arnés', 'Arneses y líneas de vida'),
            ('Zapatos seguridad', 'Zapatos y botas de seguridad'),
            ('Chaleco reflectante', 'Chalecos de alta visibilidad'),
            ('Guantes', 'Guantes de protección'),
            ('Lentes seguridad', 'Lentes y goggles de protección'),
            ('Protector auditivo', 'Protectores auditivos (orejeras, tapones)'),
            ('Respirador', 'Respiradores y mascarillas'),
            ('Ropa trabajo', 'Ropa de trabajo y overoles'),
            ('EPP', 'Elementos de protección personal (legado)'),
        ]
        for nombre, desc in tipos_ti:
            AssetType.objects.get_or_create(
                nombre=nombre,
                defaults={'descripcion': desc, 'es_ti': True},
            )
        for nombre, desc in tipos_epp:
            AssetType.objects.get_or_create(
                nombre=nombre,
                defaults={'descripcion': desc, 'es_prevencion': True},
            )

    def _crear_procesos(self, usuarios, workers, cecos):
        now = timezone.now()
        rrhh = usuarios.get('rrhh')

        p1 = crear_proceso_contratacion(rrhh, {
            'run': '20.123.456-7',
            'nombre': 'Andrés Castillo',
            'correo': 'andres.castillo@minera.cl',
            'cargo': 'Ayudante de Terreno',
            'centro_costo': cecos[0],
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
            'centro_costo': cecos[2],
            'fecha_ingreso_estimada': (now + timedelta(days=14)).date(),
            'motivo': 'Nuevo puesto creado',
        })
        for t in p2.tareas.all().order_by('orden')[:3]:
            completar_tarea(t)
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

        if len(workers) >= 6:
            p6 = crear_proceso_asignacion_activos(
                rrhh, workers[5].pk,
                'Solicitud de notebook para trabajo en terreno',
            )
            self.stdout.write(f'  Asignacion Activos TI #{p6.pk} en curso ({workers[5].nombre})')

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
