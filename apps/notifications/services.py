from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings

from .models import Notification, NotificationConfig


EVENTOS_NOTIFICABLES = [
    'proceso_inicio',
    'proceso_cierre',
    'tarea_cambio_estado',
    'tarea_proxima_vencer',
    'tarea_vencida',
    'tarea_escalada',
    'tarea_critica_bloqueo',
    'trabajador_cambio_estado_manual',
    'trabajador_edicion_bloqueada',
    'ceco_desactivacion_con_activos',
    'ceco_cambio_automatico',
    'auth_usuario_creado',
    'auth_enlace_recuperacion',
    'auth_desactivacion_con_tareas',
    'auth_sesion_por_vencer',
]


def _config_activo(tipo_evento, canal):
    try:
        config = NotificationConfig.objects.get(tipo_evento=tipo_evento, canal=canal)
        return config.activo
    except NotificationConfig.DoesNotExist:
        NotificationConfig.objects.create(
            tipo_evento=tipo_evento,
            canal=canal,
            usuario_modifico_id=1,
        )
        return True


def _crear_notificacion_interna(usuario, tipo_evento, contenido, proceso=None, tarea=None):
    if not _config_activo(tipo_evento, Notification.CanalChoices.INTERNO):
        return None

    notif = Notification.objects.create(
        tipo_evento=tipo_evento,
        contenido=contenido,
        canal=Notification.CanalChoices.INTERNO,
        estado=Notification.EstadoChoices.ENVIADA,
        fecha_envio=timezone.now(),
        usuario_destinatario=usuario,
        proceso=proceso,
        tarea=tarea,
    )
    return notif


def _enviar_email(usuario, tipo_evento, asunto, contenido_html, proceso=None, tarea=None):
    if not _config_activo(tipo_evento, Notification.CanalChoices.CORREO):
        return None

    send_mail(
        subject=asunto,
        message=contenido_html.replace('\n', '\n'),
        from_email=settings.DEFAULT_FROM_EMAIL or 'noreply@sourcingpro.cl',
        recipient_list=[usuario.email],
        fail_silently=True,
        html_message=f'<html><body style="font-family:Arial,sans-serif;padding:20px">'
                     f'{contenido_html.replace(chr(10), "<br>")}</body></html>',
    )

    Notification.objects.create(
        tipo_evento=tipo_evento,
        contenido=contenido_html,
        canal=Notification.CanalChoices.CORREO,
        estado=Notification.EstadoChoices.ENVIADA,
        fecha_envio=timezone.now(),
        usuario_destinatario=usuario,
        proceso=proceso,
        tarea=tarea,
    )


def notificar(usuario, tipo_evento, titulo, descripcion, enlace='', proceso=None, tarea=None):
    contenido = f'{titulo}\n{descripcion}' if not enlace else f'{titulo}\n{descripcion}\n{enlace}'

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
        asunto=f'SourcingPro — {titulo}',
        contenido_html=contenido,
        proceso=proceso,
        tarea=tarea,
    )
