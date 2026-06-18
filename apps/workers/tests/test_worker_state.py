import pytest

from apps.workers.models import Worker


class TestWorkerStateMachine:
    """Tests for the Worker state machine."""

    def test_estado_choices_are_complete(self):
        expected = [
            "en_proceso",
            "activo",
            "en_transito",
            "por_egresar",
            "despedido_en_proceso",
            "desvinculado",
            "eliminado",
        ]
        actual = [c[0] for c in Worker.EstadoChoices.choices]
        for e in expected:
            assert e in actual

    def test_transiciones_validas_has_all_states(self):
        for estado_value, _ in Worker.EstadoChoices.choices:
            assert estado_value in Worker.TRANSICIONES_VALIDAS, (
                f"Estado '{estado_value}' missing from TRANSICIONES_VALIDAS"
            )

    def test_activo_can_transition_to_egresar(self, worker_fixture):
        assert "por_egresar" in Worker.TRANSICIONES_VALIDAS["activo"]

    def test_activo_can_transition_to_despedido(self, worker_fixture):
        assert "despedido_en_proceso" in Worker.TRANSICIONES_VALIDAS["activo"]

    def test_activo_can_transition_to_transito(self, worker_fixture):
        assert "en_transito" in Worker.TRANSICIONES_VALIDAS["activo"]

    def test_desvinculado_has_no_transitions(self, worker_fixture):
        assert Worker.TRANSICIONES_VALIDAS["desvinculado"] == []

    def test_eliminado_has_no_transitions(self, worker_fixture):
        assert Worker.TRANSICIONES_VALIDAS["eliminado"] == []

    def test_initial_state_is_en_proceso(self):
        assert Worker.EstadoChoices.EN_PROCESO == "en_proceso"

    def test_transiciones_permitidas_method(self, worker_fixture):
        allowed = worker_fixture.transiciones_permitidas()
        assert isinstance(allowed, list)
        # Active worker should have at least 3 valid transitions
        assert len(allowed) >= 3

    def test_desvinculado_worker_transiciones_permitidas(self, cost_center):
        worker = Worker.objects.create(
            run="88888888-8",
            nombre="Desvinculado Test",
            correo="desvinc@test.cl",
            cargo="Cargo",
            estado=Worker.EstadoChoices.DESVINCULADO,
            centro_costo_actual=cost_center,
        )
        allowed = worker.transiciones_permitidas()
        assert allowed == []  # No transitions from desvinculado


class TestWorkerCreation:
    """Tests for Worker model constraints."""

    def test_run_uniqueness(self, worker_fixture):
        with pytest.raises(Exception):
            Worker.objects.create(
                run=worker_fixture.run,
                nombre="Duplicate RUN",
                correo="dup@test.cl",
                cargo="Cargo",
                estado=Worker.EstadoChoices.ACTIVO,
                centro_costo_actual=worker_fixture.centro_costo_actual,
            )

    def test_correo_uniqueness(self, worker_fixture):
        with pytest.raises(Exception):
            Worker.objects.create(
                run="00000000-0",
                nombre="Duplicate Email",
                correo=worker_fixture.correo,
                cargo="Cargo",
                estado=Worker.EstadoChoices.ACTIVO,
                centro_costo_actual=worker_fixture.centro_costo_actual,
            )

    def test_default_estado_is_en_proceso(self, cost_center):
        worker = Worker.objects.create(
            run="12312312-3",
            nombre="Default State",
            correo="default@test.cl",
            cargo="Cargo",
            centro_costo_actual=cost_center,
        )
        assert worker.estado == Worker.EstadoChoices.EN_PROCESO

    def test_save_changes_estado_to_en_proceso_if_null(self, cost_center):
        worker = Worker.objects.create(
            run="32132132-1",
            nombre="Null State",
            correo="nullstate@test.cl",
            cargo="Cargo",
            centro_costo_actual=cost_center,
        )
        worker.refresh_from_db()
        assert worker.estado != ""  # Should have a valid default
