import pytest
from django.utils import timezone

from apps.notifications.models import Notification, NotificationConfig


class TestNotificationCreation:
    """Tests for notification service functions."""

    def test_notificar_interna_creates_record(self, rrhh_user):
        from apps.notifications.services import notificar, _config_activo

        # Ensure config is active
        _config_activo("proceso_inicio", "interno")
        _config_activo("proceso_inicio", "correo")

        notificar(
            usuario=rrhh_user,
            tipo_evento="proceso_inicio",
            titulo="Test Title",
            descripcion="Test Description",
            enlace="/test/",
        )
        assert Notification.objects.filter(
            usuario_destinatario=rrhh_user,
            tipo_evento="proceso_inicio",
            canal=Notification.CanalChoices.INTERNO,
        ).exists()

    def test_notificar_email_creates_record(self, rrhh_user):
        from apps.notifications.services import notificar

        notificar(
            usuario=rrhh_user,
            tipo_evento="proceso_inicio",
            titulo="Email Test",
            descripcion="Email body",
        )
        assert Notification.objects.filter(
            usuario_destinatario=rrhh_user,
            canal=Notification.CanalChoices.CORREO,
        ).exists()

    def test_crear_notificacion_interna_respects_config(self, rrhh_user):
        from apps.notifications.services import _crear_notificacion_interna

        # Deactivate internal notifications for this event
        config = NotificationConfig.objects.filter(
            tipo_evento="tarea_cambio_estado",
            canal=Notification.CanalChoices.INTERNO,
        ).first()
        if config:
            config.activo = False
            config.usuario_modifico = rrhh_user
            config.save()
        else:
            NotificationConfig.objects.create(
                tipo_evento="tarea_cambio_estado",
                canal=Notification.CanalChoices.INTERNO,
                activo=False,
                usuario_modifico=rrhh_user,
            )
        result = _crear_notificacion_interna(
            usuario=rrhh_user,
            tipo_evento="tarea_cambio_estado",
            contenido="Should not be created",
        )
        assert result is None

    def test_config_activo_defaults_to_true(self, rrhh_user):
        from apps.notifications.services import _config_activo

        # Delete config to force auto-creation
        NotificationConfig.objects.filter(
            tipo_evento="auth_usuario_creado",
            canal="interno",
        ).delete()
        result = _config_activo("auth_usuario_creado", "interno")
        assert result is True
        config = NotificationConfig.objects.filter(
            tipo_evento="auth_usuario_creado",
            canal="interno",
        ).first()
        assert config is not None
        assert config.activo is True


class TestNotificationModel:
    """Tests for the Notification model."""

    def test_default_estado_is_pendiente(self, rrhh_user):
        notif = Notification.objects.create(
            tipo_evento="proceso_inicio",
            contenido="Test",
            canal=Notification.CanalChoices.INTERNO,
            usuario_destinatario=rrhh_user,
        )
        assert notif.estado == Notification.EstadoChoices.PENDIENTE

    def test_mark_as_read(self, rrhh_user):
        notif = Notification.objects.create(
            tipo_evento="proceso_inicio",
            contenido="Test",
            canal=Notification.CanalChoices.INTERNO,
            fecha_envio=timezone.now(),
            usuario_destinatario=rrhh_user,
        )
        notif.estado = Notification.EstadoChoices.LEIDA
        notif.save(update_fields=["estado"])
        notif.refresh_from_db()
        assert notif.estado == Notification.EstadoChoices.LEIDA

    def test_soft_delete(self, rrhh_user):
        notif = Notification.objects.create(
            tipo_evento="proceso_inicio",
            contenido="Test",
            canal=Notification.CanalChoices.INTERNO,
            usuario_destinatario=rrhh_user,
        )
        notif.estado = Notification.EstadoChoices.ELIMINADA
        notif.save(update_fields=["estado"])
        notif.refresh_from_db()
        assert notif.estado == Notification.EstadoChoices.ELIMINADA

    def test_ordering_by_fecha_envio(self, rrhh_user):
        import datetime

        Notification.objects.create(
            tipo_evento="a",
            contenido="Old",
            canal=Notification.CanalChoices.INTERNO,
            fecha_envio=timezone.now() - datetime.timedelta(days=2),
            usuario_destinatario=rrhh_user,
        )
        n2 = Notification.objects.create(
            tipo_evento="b",
            contenido="New",
            canal=Notification.CanalChoices.INTERNO,
            fecha_envio=timezone.now(),
            usuario_destinatario=rrhh_user,
        )
        notifications = Notification.objects.filter(
            usuario_destinatario=rrhh_user
        ).order_by("-fecha_envio", "-pk")
        assert notifications.first() == n2

    def test_str_representation(self, rrhh_user):
        notif = Notification.objects.create(
            tipo_evento="proceso_inicio",
            contenido="Test content",
            canal=Notification.CanalChoices.INTERNO,
            fecha_envio=timezone.now(),
            usuario_destinatario=rrhh_user,
        )
        assert "proceso_inicio" in str(notif)
        assert rrhh_user.nombre in str(notif)


class TestNotificationConfig:
    """Tests for NotificationConfig model."""

    def test_unique_together(self, rrhh_user):
        NotificationConfig.objects.create(
            tipo_evento="proceso_inicio",
            canal=Notification.CanalChoices.INTERNO,
            usuario_modifico=rrhh_user,
        )
        with pytest.raises(Exception):
            NotificationConfig.objects.create(
                tipo_evento="proceso_inicio",
                canal=Notification.CanalChoices.INTERNO,
                usuario_modifico=rrhh_user,
            )

    def test_default_activo(self, rrhh_user):
        config = NotificationConfig.objects.create(
            tipo_evento="proceso_inicio",
            canal=Notification.CanalChoices.CORREO,
            usuario_modifico=rrhh_user,
        )
        assert config.activo is True

    def test_different_channels_allowed(self, rrhh_user):
        c1 = NotificationConfig.objects.create(
            tipo_evento="proceso_inicio",
            canal=Notification.CanalChoices.INTERNO,
            usuario_modifico=rrhh_user,
        )
        c2 = NotificationConfig.objects.create(
            tipo_evento="proceso_inicio",
            canal=Notification.CanalChoices.CORREO,
            usuario_modifico=rrhh_user,
        )
        assert c1.pk != c2.pk
