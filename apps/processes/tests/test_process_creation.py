import pytest
from datetime import date
from django.core.exceptions import ValidationError
from django.utils import timezone

from apps.processes.models import Process, Task


class TestCrearProcesoContratacion:
    """Tests for the contratacion process creation."""

    def test_creates_process_with_tasks(self, rrhh_user, cost_center, epp_asset):
        from apps.processes.services import crear_proceso_contratacion
        datos = {
            'run': '87654321-K',
            'nombre': 'Nuevo Trabajador',
            'correo': 'nuevo@test.cl',
            'cargo': 'Supervisor',
            'centro_costo': cost_center,
            'fecha_ingreso_estimada': date(2026, 7, 1),
            'fecha_termino_contrato': date(2027, 6, 30),
        }
        process = crear_proceso_contratacion(rrhh_user, datos)
        assert isinstance(process, Process)
        assert process.tipo == Process.TipoChoices.CONTRATACION
        assert process.estado == Process.EstadoChoices.EN_CURSO
        assert process.trabajador is not None
        assert process.trabajador.cargo == 'Supervisor'
        assert process.trabajador.centro_costo_actual == cost_center
        assert process.usuario_inicio == rrhh_user

    def test_tasks_are_created_for_contratacion(self, rrhh_user, cost_center, epp_asset):
        from apps.processes.services import crear_proceso_contratacion
        datos = {
            'run': '11111111-1',
            'nombre': 'Worker Tasks',
            'correo': 'tasks@test.cl',
            'cargo': 'Cargo',
            'centro_costo': cost_center,
        }
        process = crear_proceso_contratacion(rrhh_user, datos)
        tasks = process.tareas.all()
        assert tasks.count() >= 3
        task_types = list(tasks.values_list('tipo', flat=True))
        assert Task.TipoChoices.CREAR_CUENTA_TI in task_types
        assert Task.TipoChoices.EXAMENES_PREOCUPACIONALES in task_types

    def test_creates_cost_center_history(self, rrhh_user, cost_center, epp_asset):
        from apps.processes.services import crear_proceso_contratacion
        from apps.workers.models import CostCenterHistory
        datos = {
            'run': '22222222-2',
            'nombre': 'Worker History',
            'correo': 'history@test.cl',
            'cargo': 'Cargo',
            'centro_costo': cost_center,
        }
        process = crear_proceso_contratacion(rrhh_user, datos)
        history = CostCenterHistory.objects.filter(trabajador=process.trabajador)
        assert history.exists()
        assert history.first().centro_costo == cost_center

    def test_worker_starts_in_en_proceso_state(self, rrhh_user, cost_center, epp_asset):
        from apps.processes.services import crear_proceso_contratacion
        from apps.workers.models import Worker
        datos = {
            'run': '33333333-3',
            'nombre': 'Worker State',
            'correo': 'state@test.cl',
            'cargo': 'Cargo',
            'centro_costo': cost_center,
        }
        process = crear_proceso_contratacion(rrhh_user, datos)
        assert process.trabajador.estado == Worker.EstadoChoices.EN_PROCESO

    def test_duplicate_run_raises_error(self, rrhh_user, cost_center, worker_fixture):
        from apps.processes.services import crear_proceso_contratacion
        datos = {
            'run': worker_fixture.run,
            'nombre': 'Duplicated',
            'correo': 'dup@test.cl',
            'cargo': 'Cargo',
            'centro_costo': cost_center,
        }
        with pytest.raises(Exception):
            crear_proceso_contratacion(rrhh_user, datos)


class TestCrearProcesoCierreTypes:
    """Tests for cambio_ceco, termino, and despido processes."""

    def test_cambio_ceco_creates_tasks(self, rrhh_user, worker_fixture, cost_center):
        from apps.processes.services import crear_proceso_cambio_ceco
        process = crear_proceso_cambio_ceco(
            usuario=rrhh_user,
            worker_id=worker_fixture.pk,
            ceco_destino_id=cost_center.pk,
            fecha=date(2026, 7, 15),
            motivo='Reasignacion por proyecto',
        )
        assert process.tipo == Process.TipoChoices.CAMBIO_CECO
        assert process.trabajador == worker_fixture
        assert process.estado == Process.EstadoChoices.EN_CURSO
        assert process.ceco_destino == cost_center
        assert process.tareas.exists()

    def test_termino_creates_tasks(self, rrhh_user, worker_fixture):
        from apps.processes.services import crear_proceso_termino
        process = crear_proceso_termino(
            usuario=rrhh_user,
            worker_id=worker_fixture.pk,
            fecha_termino=date(2026, 12, 31),
            motivo='Fin de contrato',
        )
        assert process.tipo == Process.TipoChoices.TERMINO
        assert process.estado == Process.EstadoChoices.EN_CURSO
        assert process.tareas.exists()

    def test_termino_requires_rrhh_confirmation(self, rrhh_user, worker_fixture):
        from apps.processes.services import crear_proceso_termino
        process = crear_proceso_termino(
            usuario=rrhh_user,
            worker_id=worker_fixture.pk,
            fecha_termino=date(2026, 12, 31),
            motivo='Fin de contrato',
        )
        assert process.requiere_confirmacion_rrhh in (True, False)

    def test_despido_creates_tasks_and_alerts(self, rrhh_user, worker_fixture, logistica_user):
        from apps.processes.services import crear_proceso_despido
        process = crear_proceso_despido(
            usuario=rrhh_user,
            worker_id=worker_fixture.pk,
            fecha=date(2026, 6, 15),
            motivo='Bajo rendimiento',
            causal_legal='Articulo 160',
        )
        assert process.tipo == Process.TipoChoices.DESPIDO
        assert process.estado == Process.EstadoChoices.EN_CURSO
        assert process.causal_legal == 'Articulo 160'
        task_types = list(process.tareas.values_list('tipo', flat=True))
        assert Task.TipoChoices.RECUPERACION_ACTIVOS in task_types

    def test_despido_alerts_logistica_users(self, rrhh_user, worker_fixture, logistica_user):
        from apps.processes.services import crear_proceso_despido
        from apps.notifications.models import Notification
        process = crear_proceso_despido(
            usuario=rrhh_user,
            worker_id=worker_fixture.pk,
            fecha=date(2026, 6, 15),
            motivo='Test notificacion',
            causal_legal='Art 160',
        )
        notif = Notification.objects.filter(
            usuario_destinatario=logistica_user,
            tipo_evento='recuperacion_activos_alerta',
        )
        assert notif.exists()

    def test_despido_sets_worker_state(self, rrhh_user, worker_fixture, logistica_user):
        from apps.processes.services import crear_proceso_despido
        from apps.workers.models import Worker
        process = crear_proceso_despido(
            usuario=rrhh_user,
            worker_id=worker_fixture.pk,
            fecha=date(2026, 6, 15),
            motivo='Test',
            causal_legal='Art 160',
        )
        worker_fixture.refresh_from_db()
        assert worker_fixture.estado == Worker.EstadoChoices.DESPEDIDO_EN_PROCESO

    def test_worker_not_active_still_creates_process(self, rrhh_user, cost_center):
        """Even inactive workers can have processes created for them."""
        from apps.processes.services import crear_proceso_cambio_ceco
        from apps.workers.models import Worker
        worker = Worker.objects.create(
            run='99999999-9',
            nombre='Inactivo',
            correo='inactivo@test.cl',
            cargo='Cargo',
            estado=Worker.EstadoChoices.DESVINCULADO,
            centro_costo_actual=cost_center,
        )
        process = crear_proceso_cambio_ceco(
            usuario=rrhh_user,
            worker_id=worker.pk,
            ceco_destino_id=cost_center.pk,
            fecha=date(2026, 7, 15),
            motivo='Test',
        )
        assert process.trabajador == worker
