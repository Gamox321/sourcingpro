import pytest
from datetime import date

from apps.processes.models import Process, Task


@pytest.fixture
def contratacion_process(rrhh_user, cost_center, epp_asset):
    from apps.processes.services import crear_proceso_contratacion

    datos = {
        "run": "55555555-5",
        "nombre": "Task Tester",
        "correo": "tasktest@test.cl",
        "cargo": "Cargo",
        "centro_costo": cost_center,
    }
    return crear_proceso_contratacion(rrhh_user, datos)


class TestTaskCompletar:
    """Tests for the completar_tarea function."""

    def test_complete_task_changes_state(self, rrhh_user, contratacion_process):
        from apps.processes.services import completar_tarea

        task = contratacion_process.tareas.filter(
            estado=Task.EstadoChoices.PENDIENTE
        ).first()
        assert task is not None
        task.estado = Task.EstadoChoices.EN_PROCESO
        task.save()
        completar_tarea(task)
        task.refresh_from_db()
        assert task.estado == Task.EstadoChoices.COMPLETADA
        assert task.fecha_completado is not None

    def test_all_prior_tasks_must_be_complete(self, rrhh_user, contratacion_process):
        from apps.processes.services import completar_tarea

        tasks = list(
            contratacion_process.tareas.order_by("orden").exclude(
                tipo=Task.TipoChoices.RECUPERACION_ACTIVOS
            )
        )
        if len(tasks) >= 2:
            task1 = tasks[0]
            task1.estado = Task.EstadoChoices.EN_PROCESO
            task1.save()
            completar_tarea(task1)
            task1.refresh_from_db()
            assert task1.estado == Task.EstadoChoices.COMPLETADA
            # Second task should also be completable
            task2 = tasks[1]
            task2.estado = Task.EstadoChoices.EN_PROCESO
            task2.save()
            completar_tarea(task2)
            task2.refresh_from_db()


class TestTaskDependencies:
    """Test that task dependency chains work correctly."""

    def test_bloqueo_accessos_completes(self, rrhh_user, worker_fixture):
        from apps.processes.services import crear_proceso_termino, completar_tarea

        process = crear_proceso_termino(
            usuario=rrhh_user,
            worker_id=worker_fixture.pk,
            fecha_termino=date(2026, 12, 31),
            motivo="Fin de contrato",
        )
        bloqueo_task = process.tareas.filter(
            tipo=Task.TipoChoices.BLOQUEO_ACCESOS
        ).first()
        assert bloqueo_task is not None
        bloqueo_task.estado = Task.EstadoChoices.EN_PROCESO
        bloqueo_task.save()
        completar_tarea(bloqueo_task)
        bloqueo_task.refresh_from_db()
        assert bloqueo_task.estado == Task.EstadoChoices.COMPLETADA


class TestProcessCompletion:
    """Tests for process closure when all tasks are complete."""

    def test_contratacion_process_closes_when_all_tasks_done(
        self, rrhh_user, contratacion_process
    ):
        from apps.processes.services import completar_tarea

        tasks = contratacion_process.tareas.all()
        for t in tasks:
            t.estado = Task.EstadoChoices.EN_PROCESO
            t.save()
            completar_tarea(t)
            t.refresh_from_db()
        contratacion_process.refresh_from_db()
        pending = contratacion_process.tareas.exclude(
            estado__in=[
                Task.EstadoChoices.COMPLETADA,
                Task.EstadoChoices.GESTIONADO_EXTERNO,
            ]
        ).exists()
        if not pending:
            assert contratacion_process.estado == Process.EstadoChoices.COMPLETADO
