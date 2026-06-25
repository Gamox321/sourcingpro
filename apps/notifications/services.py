from django.utils import timezone
from django.utils.html import strip_tags
from django.core.mail import send_mail
from django.conf import settings

from apps.audit.middleware import get_current_user
from .models import Notification, NotificationConfig


EVENTOS_NOTIFICABLES = [
    "proceso_inicio",
    "proceso_cierre",
    "proceso_despido_inicio",
    "tarea_cambio_estado",
    "tarea_proxima_vencer",
    "tarea_vencida",
    "tarea_escalada",
    "tarea_critica_bloqueo",
    "recuperacion_activos_alerta",
    "trabajador_cambio_estado_manual",
    "trabajador_edicion_bloqueada",
    "ceco_desactivacion_con_activos",
    "ceco_cambio_automatico",
    "auth_usuario_creado",
    "auth_enlace_recuperacion",
    "auth_desactivacion_con_tareas",
    "auth_sesion_por_vencer",
    "devolucion_incompleta",
    "devolucion_validada",
]


def _get_config_owner():
    user = get_current_user()
    if user is not None and user.is_authenticated:
        return user
    from apps.accounts.models import User

    return (
        User.objects.filter(roles__nombre="administrador", is_active=True).first()
        or User.objects.first()
    )


def _config_activo(tipo_evento, canal):
    try:
        config = NotificationConfig.objects.get(tipo_evento=tipo_evento, canal=canal)
        return config.activo
    except NotificationConfig.DoesNotExist:
        NotificationConfig.objects.create(
            tipo_evento=tipo_evento,
            canal=canal,
            usuario_modifico=_get_config_owner(),
        )
        return True


def _crear_notificacion(usuario, tipo_evento, contenido, canal, proceso, tarea):
    Notification.objects.create(
        tipo_evento=tipo_evento,
        contenido=contenido,
        canal=canal,
        estado=Notification.EstadoChoices.ENVIADA,
        fecha_envio=timezone.now(),
        usuario_destinatario=usuario,
        proceso=proceso,
        tarea=tarea,
    )


def _crear_notificacion_interna(
    usuario, tipo_evento, contenido, proceso=None, tarea=None
):
    if not _config_activo(tipo_evento, Notification.CanalChoices.INTERNO):
        return None
    _crear_notificacion(
        usuario,
        tipo_evento,
        contenido,
        Notification.CanalChoices.INTERNO,
        proceso,
        tarea,
    )


def _enviar_email(
    usuario, tipo_evento, asunto, contenido_html, proceso=None, tarea=None
):
    if not _config_activo(tipo_evento, Notification.CanalChoices.CORREO):
        return None

    send_mail(
        subject=asunto,
        message=strip_tags(contenido_html),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[usuario.email],
        fail_silently=True,
        html_message=f'<html><body style="font-family:Arial,sans-serif;padding:20px">'
        f"{contenido_html.replace(chr(10), '<br>')}</body></html>",
    )

    _crear_notificacion(
        usuario,
        tipo_evento,
        contenido_html,
        Notification.CanalChoices.CORREO,
        proceso,
        tarea,
    )


def notificar(
    usuario, tipo_evento, titulo, descripcion, enlace="", proceso=None, tarea=None
):
    contenido = (
        f"{titulo}\n{descripcion}"
        if not enlace
        else f"{titulo}\n{descripcion}\n{enlace}"
    )

    _crear_notificacion_interna(
        usuario=usuario,
        tipo_evento=tipo_evento,
        contenido=contenido,
        proceso=proceso,
        tarea=tarea,
    )

    _enviar_email(
        usuario=usuario,
        tipo_evento=tipo_evento,
        asunto=f"SourcingPro — {titulo}",
        contenido_html=contenido,
        proceso=proceso,
        tarea=tarea,
    )
