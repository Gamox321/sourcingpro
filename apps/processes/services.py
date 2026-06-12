import datetime
import logging

from django.db import transaction
from django.utils import timezone

from apps.accounts.models import User, Role
from apps.workers.models import Worker, CostCenterHistory
from apps.inventory.models import Asset, AssetAssignment
from .models import Process, Task

logger = logging.getLogger(__name__)


def _notificar_tarea(task, tipo_evento='tarea_cambio_estado'):
    from apps.notifications.services import notificar
    usuario = task.usuario_responsable
    if not usuario:
        return
    notificar(
        usuario=usuario,
        tipo_evento=tipo_evento,
        titulo=f'Tarea: {task.get_tipo_display()}',
        descripcion=f'Estado: {task.get_estado_display()}. '
                    f'Trabajador: {task.proceso.trabajador.nombre}. '
                    f'Proceso #{task.proceso.pk}',
        enlace='',
        proceso=task.proceso,
        tarea=task,
    )


def _notificar_iniciador(proceso, tipo_evento, titulo, descripcion):
    from apps.notifications.services import notificar
    notificar(
        usuario=proceso.usuario_inicio,
        tipo_evento=tipo_evento,
        titulo=titulo,
        descripcion=descripcion,
        enlace='',
        proceso=proceso,
    )


def _find_user_for_role(role_name):
    user = User.objects.filter(
        is_active=True, roles__nombre=role_name
    ).distinct().first()
    if user is None:
        logger.warning(
            'No active user found for role "%s". Tasks of this type will be orphaned '
            '(usuario_responsable=None). Run seed_demo or create a user with this role.',
            role_name,
        )
    return user


def _make_aware(dt):
    if dt is None:
        return None
    if isinstance(dt, datetime.date) and not isinstance(dt, datetime.datetime):
        return timezone.make_aware(
            datetime.datetime.combine(dt, datetime.time(23, 59)),
        )
    if timezone.is_naive(dt):
        return timezone.make_aware(dt)
    return dt


def _create_task(proceso, tipo, descripcion=None, urgencia='normal',
                 plazo_limite=None, omitida=False, motivo_omision=None, orden=0):
    from .models import TaskDeadlineConfig
    from apps.audit.models import AuditLog

    role_name = Task.TIPO_AREA_MAP.get(tipo)
    responsable = _find_user_for_role(role_name) if role_name else None

    # Obtener configuración de plazo si existe
    try:
        config = TaskDeadlineConfig.objects.get(tipo_tarea=tipo)
        if plazo_limite is None:
            plazo_limite = timezone.now() + datetime.timedelta(days=config.plazo_dias)
        if config.es_critica:
            urgencia = Task.UrgenciaChoices.CRITICA
    except TaskDeadlineConfig.DoesNotExist:
        # Usar valores por defecto si no hay configuración
        if plazo_limite is None:
            plazo_limite = timezone.now() + datetime.timedelta(days=5)

    task = Task.objects.create(
        proceso=proceso,
        tipo=tipo,
        urgencia=urgencia,
        descripcion=descripcion,
        plazo_limite=_make_aware(plazo_limite),
        omitida=omitida,
        motivo_omision=motivo_omision,
        orden=orden,
        usuario_responsable=responsable,
    )
    
    # Registrar creación de tarea en bitácora
    AuditLog.objects.create(
        tabla_afectada='tarea',
        accion=AuditLog.AccionChoices.CREACION,
        descripcion=f'Tarea {dict(Task.TipoChoices.choices).get(tipo, tipo)} creada',
        valor_nuevo={'tipo': tipo, 'urgencia': urgencia, 'responsable': responsable.email if responsable else None},
        usuario=proceso.usuario_inicio,
        id_entidad_afectada=task.pk,
    )

    return task


@transaction.atomic
def crear_proceso_contratacion(usuario, datos_worker):
    from apps.clients.models import CostCenter
    from apps.audit.models import AuditLog
    
    ceco = datos_worker['centro_costo']

    worker = Worker.objects.create(
        run=datos_worker['run'],
        nombre=datos_worker['nombre'],
        correo=datos_worker['correo'],
        cargo=datos_worker['cargo'],
        fecha_ingreso_estimada=datos_worker.get('fecha_ingreso_estimada'),
        centro_costo_actual=ceco,
        estado=Worker.EstadoChoices.EN_PROCESO,
    )

    proceso = Process.objects.create(
        tipo=Process.TipoChoices.CONTRATACION,
        trabajador=worker,
        usuario_inicio=usuario,
        ceco_origen=ceco,
        ceco_destino=None,
        motivo=datos_worker.get('motivo', ''),
    )
    
    CostCenterHistory.objects.create(
        trabajador=worker,
        centro_costo=ceco,
        fecha_inicio=timezone.now().date(),
        proceso=proceso,
    )
    
    # Registrar creación de proceso en bitácora
    AuditLog.objects.create(
        tabla_afectada='proceso',
        accion=AuditLog.AccionChoices.CREACION,
        descripcion=f'Proceso de contratación iniciado para {worker.nombre}',
        valor_nuevo={'tipo': 'contratacion', 'trabajador': worker.nombre, 'ceco': ceco.nombre},
        usuario=usuario,
        id_entidad_afectada=proceso.pk,
    )

    _create_task(proceso, Task.TipoChoices.CREAR_CUENTA_TI,
                 'Crear cuenta corporativa y accesos según cargo.', orden=1)
    _create_task(proceso, Task.TipoChoices.EXAMENES_PREOCUPACIONALES,
                 'Gestionar exámenes pre-ocupacionales.', orden=2)
    _create_task(proceso, Task.TipoChoices.EPP_INDUCCION,
                 'Entregar EPP y realizar inducción.', orden=3)
    _create_task(proceso, Task.TipoChoices.EQUIPAMIENTO,
                 'Entregar equipamiento según cargo.', orden=4)

    _notificar_iniciador(
        proceso, 'proceso_inicio',
        f'Proceso de {proceso.get_tipo_display()} iniciado',
        f'Trabajador: {worker.nombre}. Se generaron {proceso.tareas.count()} tareas.'
    )
    for t in proceso.tareas.all():
        _notificar_tarea(t, 'tarea_cambio_estado')

    return proceso


@transaction.atomic
def crear_proceso_cambio_ceco(usuario, worker_id, ceco_destino_id, fecha, motivo):
    from apps.clients.models import CostCenter
    worker = Worker.objects.get(pk=worker_id)
    ceco_destino = CostCenter.objects.get(pk=ceco_destino_id)

    proceso = Process.objects.create(
        tipo=Process.TipoChoices.CAMBIO_CECO,
        trabajador=worker,
        usuario_inicio=usuario,
        ceco_origen=worker.centro_costo_actual,
        ceco_destino=ceco_destino,
        motivo=motivo,
    )

    worker.estado = Worker.EstadoChoices.EN_TRANSITO
    worker.save(update_fields=['estado'])

    activos_asignados = AssetAssignment.objects.filter(
        trabajador=worker, fecha_devolucion__isnull=True
    ).select_related('activo')

    if activos_asignados.exists():
        _create_task(proceso, Task.TipoChoices.DEVOLUCION_ACTIVOS,
                     'Devolver activos asignados en CeCo de origen.',
                     plazo_limite=fecha)
        for aa in activos_asignados:
            aa.activo.cambiar_estado(Asset.EstadoChoices.PENDIENTE_DEVOLUCION)
    else:
        _generar_reincorporacion_cambio_ceco(proceso, worker, ceco_destino, fecha)

    _notificar_iniciador(
        proceso, 'proceso_inicio',
        f'Cambio de CeCo iniciado',
        f'Trabajador: {worker.nombre} → {ceco_destino.nombre}'
    )
    for t in proceso.tareas.all():
        _notificar_tarea(t, 'tarea_cambio_estado')

    return proceso


def _generar_reincorporacion_cambio_ceco(proceso, worker, ceco_destino, fecha):
    _create_task(proceso, Task.TipoChoices.CREAR_CUENTA_TI,
                 'Actualizar accesos y cuenta para nuevo CeCo.',
                 plazo_limite=fecha)

    from apps.inventory.models import AssetType
    epp_type = AssetType.objects.filter(nombre='EPP').first()
    tiene_epp_destino = False
    if epp_type:
        tiene_epp_destino = Asset.objects.filter(
            tipo=epp_type, estado=Asset.EstadoChoices.DISPONIBLE
        ).exists()

    if tiene_epp_destino:
        _create_task(proceso, Task.TipoChoices.EPP_INDUCCION,
                     'Evaluar necesidad de EPP específico del nuevo CeCo.',
                     plazo_limite=fecha)
    else:
        _create_task(proceso, Task.TipoChoices.EPP_INDUCCION,
                     'EPP específico del nuevo CeCo (omitido si vigente).',
                     plazo_limite=fecha, omitida=True,
                     motivo_omision='Certificaciones vigentes')

    _create_task(proceso, Task.TipoChoices.EQUIPAMIENTO,
                 'Asignar equipamiento del nuevo CeCo.',
                 plazo_limite=fecha)


def _completar_devolucion_cambio_ceco(proceso):
    """
    RF-13: Valida que TODOS los activos hayan sido devueltos antes de avanzar.
    Solo se llama cuando la tarea de devolución está completada.
    """
    worker = proceso.trabajador
    
    # Verificar que no queden activos pendientes de devolución
    activos_pendientes = AssetAssignment.objects.filter(
        trabajador=worker,
        fecha_devolucion__isnull=True,
        activo__estado=Asset.EstadoChoices.PENDIENTE_DEVOLUCION,
    ).count()
    
    if activos_pendientes > 0:
        # No avanzar si hay activos pendientes (RF-13)
        from apps.notifications.services import notificar
        notificar(
            usuario=proceso.usuario_inicio,
            tipo_evento='devolucion_incompleta',
            titulo=f'Devolución Incompleta — {worker.nombre}',
            descripcion=f'Hay {activos_pendientes} activo(s) pendiente(s) de devolución. '
                        f'No se puede avanzar a la reincorporación en el nuevo CeCo.',
            proceso=proceso,
        )
        return False
    
    ceco_destino = proceso.ceco_destino
    fecha = timezone.now()

    CostCenterHistory.objects.create(
        trabajador=worker,
        centro_costo=ceco_destino,
        fecha_inicio=fecha.date(),
        proceso=proceso,
    )

    _generar_reincorporacion_cambio_ceco(proceso, worker, ceco_destino, fecha)
    
    # Notificar éxito de validación (RF-14)
    from apps.notifications.services import notificar
    notificar(
        usuario=proceso.usuario_inicio,
        tipo_evento='devolucion_validada',
        titulo=f'Devolución Validada — {worker.nombre}',
        descripcion=f'Todos los activos fueron devueltos correctamente. '
                    f'Iniciando reincorporación en {ceco_destino.nombre}.',
        proceso=proceso,
    )
    
    return True


@transaction.atomic
def crear_proceso_termino(usuario, worker_id, fecha_termino, motivo):
    worker = Worker.objects.get(pk=worker_id)

    proceso = Process.objects.create(
        tipo=Process.TipoChoices.TERMINO,
        trabajador=worker,
        usuario_inicio=usuario,
        ceco_origen=worker.centro_costo_actual,
        motivo=motivo,
    )

    worker.estado = Worker.EstadoChoices.POR_EGRESAR
    worker.save(update_fields=['estado'])

    _create_task(proceso, Task.TipoChoices.DEVOLUCION_ACTIVOS,
                 'Gestionar devolución de activos asignados.',
                 plazo_limite=fecha_termino, orden=1)
    _create_task(proceso, Task.TipoChoices.PREPARAR_BLOQUEO_ACCESOS,
                 'Preparar bloqueo de cuenta y accesos para fecha de término.',
                 plazo_limite=fecha_termino, orden=2)
    _create_task(proceso, Task.TipoChoices.FINIQUITO_COORDINACION,
                 'Coordinar finiquito en sistema externo.',
                 plazo_limite=fecha_termino, orden=3)
    _create_task(proceso, Task.TipoChoices.BLOQUEO_ACCESOS,
                 'Bloquear accesos del trabajador tras finiquito.',
                 plazo_limite=fecha_termino, orden=4)

    _notificar_iniciador(
        proceso, 'proceso_inicio',
        f'Término de contrato iniciado',
        f'Trabajador: {worker.nombre}. Fecha término: {fecha_termino}.'
    )
    for t in proceso.tareas.all():
        _notificar_tarea(t, 'tarea_cambio_estado')

    return proceso


@transaction.atomic
def crear_proceso_despido(usuario, worker_id, fecha, motivo, causal_legal):
    worker = Worker.objects.get(pk=worker_id)

    proceso = Process.objects.create(
        tipo=Process.TipoChoices.DESPIDO,
        trabajador=worker,
        usuario_inicio=usuario,
        ceco_origen=worker.centro_costo_actual,
        motivo=motivo,
        causal_legal=causal_legal,
        requiere_confirmacion_rrhh=True,
    )

    worker.estado = Worker.EstadoChoices.DESPEDIDO_EN_PROCESO
    worker.save(update_fields=['estado'])

    # Bloquear acceso del usuario con mismo correo
    try:
        user_linked = User.objects.get(email=worker.correo)
        user_linked.is_active = False
        user_linked.save(update_fields=['is_active'])
    except User.DoesNotExist:
        pass

    _create_task(proceso, Task.TipoChoices.RECUPERACION_ACTIVOS,
                 'Recuperar todos los activos asignados al trabajador.',
                 urgencia=Task.UrgenciaChoices.CRITICA,
                 plazo_limite=fecha, orden=1)
    _create_task(proceso, Task.TipoChoices.BLOQUEO_ACCESOS,
                 'Bloquear todos los accesos y cuentas del trabajador.',
                 urgencia=Task.UrgenciaChoices.CRITICA,
                 plazo_limite=fecha, orden=2)
    _create_task(proceso, Task.TipoChoices.FINIQUITO_COORDINACION,
                 'Coordinar finiquito y descuentos en sistema externo.',
                 plazo_limite=fecha, orden=3)

    asignaciones = AssetAssignment.objects.filter(
        trabajador=worker, fecha_devolucion__isnull=True
    ).select_related('activo')
    for aa in asignaciones:
        aa.activo.cambiar_estado(Asset.EstadoChoices.PENDIENTE_DEVOLUCION)

    # Notificaciones por email a roles involucrados
    from apps.notifications.services import notificar

    # Email a TI (BLOQUEO_ACCESOS task)
    ti_user = _find_user_for_role('ti')
    if ti_user:
        notificar(
            usuario=ti_user,
            tipo_evento='proceso_despido_inicio',
            titulo=f'Despido iniciado — Bloqueo inmediato requerido',
            descripcion=f'Se ha iniciado proceso de despido para {worker.nombre}. '
                        f'Debe bloquear todos los accesos y cuentas de forma inmediata.',
            enlace='',
            proceso=proceso,
        )

    # Email a Finanzas (FINIQUITO_COORDINACION task)
    finanzas_user = _find_user_for_role('finanzas')
    if finanzas_user:
        notificar(
            usuario=finanzas_user,
            tipo_evento='proceso_despido_inicio',
            titulo=f'Despido iniciado — Coordinar finiquito',
            descripcion=f'Se ha iniciado proceso de despido para {worker.nombre}. '
                        f'Debe coordinar el finiquito y descuentos en sistema externo.',
            enlace='',
            proceso=proceso,
        )

    # Email a RRHH
    rrhh_user = _find_user_for_role('rrhh')
    if rrhh_user:
        notificar(
            usuario=rrhh_user,
            tipo_evento='proceso_despido_inicio',
            titulo=f'Despido iniciado — {worker.nombre}',
            descripcion=f'Se ha iniciado proceso de despido. Causal: {causal_legal}. '
                        f'Trabajador: {worker.nombre}. Revise el proceso en el sistema.',
            enlace='',
            proceso=proceso,
        )

    # Alertar a Logistica para recuperar activos
    try:
        logistica_users = User.objects.filter(
            roles__nombre=Role.RoleChoices.LOGISTICA,
            is_active=True
        ).distinct()
        for logistica_user in logistica_users:
            notificar(
                usuario=logistica_user,
                tipo_evento='recuperacion_activos_alerta',
                titulo=f'Recuperación de activos — {worker.nombre}',
                descripcion=f'Proceso de despido iniciado para {worker.nombre}. '
                            f'Favor contactar para recuperar equipos (PC, tablet, etc.).',
                enlace='',
                proceso=proceso,
            )
    except Exception:
        pass

    _notificar_iniciador(
        proceso, 'proceso_inicio',
        f'Despido iniciado — {worker.nombre}',
        f'Causal: {causal_legal}. Se requiere bloqueo inmediato.'
    )
    for t in proceso.tareas.all():
        _notificar_tarea(t, 'tarea_cambio_estado')

    return proceso


def completar_tarea(task):
    from django.utils import timezone
    from apps.audit.models import AuditLog
    
    task.estado = Task.EstadoChoices.COMPLETADA
    task.fecha_completado = timezone.now()
    task.save(update_fields=['estado', 'fecha_completado'])
    
    # Registrar en bitácora (RF-08/RF-17/RF-26/RF-35)
    AuditLog.objects.create(
        tabla_afectada='tarea',
        accion=AuditLog.AccionChoices.CAMBIO_ESTADO,
        descripcion=f'Tarea {task.get_tipo_display()} completada',
        valor_anterior={'estado': Task.EstadoChoices.EN_PROCESO},
        valor_nuevo={'estado': Task.EstadoChoices.COMPLETADA, 'fecha_completado': str(task.fecha_completado)},
        usuario=task.usuario_responsable or task.proceso.usuario_inicio,
        id_entidad_afectada=task.pk,
    )

    # RF-13: Validar devolución completa en cambio de CeCo
    if (task.tipo == Task.TipoChoices.DEVOLUCION_ACTIVOS
            and task.proceso.tipo == Process.TipoChoices.CAMBIO_CECO):
        devolucion_completa = _completar_devolucion_cambio_ceco(task.proceso)
        if not devolucion_completa:
            # No notificar éxito ni verificar completion del proceso si hay activos pendientes
            return task

    _notificar_iniciador(
        task.proceso, 'tarea_cambio_estado',
        f'Tarea completada: {task.get_tipo_display()}',
        f'Trabajador: {task.proceso.trabajador.nombre}. Proceso #{task.proceso.pk}'
    )

    _check_process_completion(task.proceso)
    return task


def completar_tarea_con_activos(task, asset_ids):
    worker = task.proceso.trabajador
    assigned = []
    for asset_id in asset_ids:
        asset = Asset.objects.filter(pk=asset_id, estado='disponible').first()
        if not asset:
            continue
        AssetAssignment.objects.create(
            activo=asset,
            trabajador=worker,
            proceso=task.proceso,
        )
        asset.cambiar_estado(Asset.EstadoChoices.ASIGNADO)
        assigned.append(asset.codigo)
    completar_tarea(task)
    return assigned


def gestionar_externamente_tarea(task):
    from django.utils import timezone
    task.estado = Task.EstadoChoices.GESTIONADO_EXTERNO
    task.fecha_completado = timezone.now()
    task.save(update_fields=['estado', 'fecha_completado'])

    _notificar_iniciador(
        task.proceso, 'tarea_cambio_estado',
        f'Tarea gestionada externamente: {task.get_tipo_display()}',
        f'Trabajador: {task.proceso.trabajador.nombre}. Proceso #{task.proceso.pk}'
    )

    _check_process_completion(task.proceso)
    return task


def _check_process_completion(proceso):
    if proceso.estado != Process.EstadoChoices.EN_CURSO:
        return

    tareas = proceso.tareas.all()
    pendientes = tareas.exclude(
        estado__in=[Task.EstadoChoices.COMPLETADA,
                    Task.EstadoChoices.GESTIONADO_EXTERNO,
                    Task.EstadoChoices.ESCALADA]
    ).exclude(omitida=True)

    if not pendientes.exists():
        if proceso.tipo == Process.TipoChoices.TERMINO:
            return

        if proceso.tipo == Process.TipoChoices.DESPIDO:
            proceso.requiere_confirmacion_rrhh = True
            proceso.save(update_fields=['requiere_confirmacion_rrhh'])
            return

        _finalizar_proceso(proceso)


def finalizar_proceso_manual(proceso):
    _finalizar_proceso(proceso)


def _finalizar_proceso(proceso):
    from django.utils import timezone
    from apps.audit.models import AuditLog
    
    worker = proceso.trabajador

    if proceso.tipo == Process.TipoChoices.CONTRATACION:
        worker.estado = Worker.EstadoChoices.ACTIVO
        worker.fecha_ingreso_efectiva = timezone.now().date()
        worker.save(update_fields=['estado', 'fecha_ingreso_efectiva'])

    elif proceso.tipo == Process.TipoChoices.CAMBIO_CECO:
        worker.estado = Worker.EstadoChoices.ACTIVO
        worker.centro_costo_actual = proceso.ceco_destino
        worker.save(update_fields=['estado', 'centro_costo_actual'])

    elif proceso.tipo in (Process.TipoChoices.TERMINO, Process.TipoChoices.DESPIDO):
        worker.estado = Worker.EstadoChoices.DESVINCULADO
        worker.save(update_fields=['estado'])

    proceso.estado = Process.EstadoChoices.COMPLETADO
    proceso.fecha_cierre = timezone.now()
    proceso.save(update_fields=['estado', 'fecha_cierre'])
    
    # Registrar en bitácora de auditoría (RF-08/RF-17/RF-26/RF-35)
    AuditLog.objects.create(
        tabla_afectada='proceso',
        accion=AuditLog.AccionChoices.CIERRE,
        descripcion=f'Proceso de {proceso.get_tipo_display()} completado. Trabajador: {worker.get_estado_display()}',
        valor_anterior={'estado': Process.EstadoChoices.EN_CURSO},
        valor_nuevo={'estado': Process.EstadoChoices.COMPLETADO, 'fecha_cierre': str(proceso.fecha_cierre)},
        usuario=proceso.usuario_inicio,
        id_entidad_afectada=proceso.pk,
    )

    _notificar_iniciador(
        proceso, 'proceso_cierre',
        f'Proceso completado: {proceso.get_tipo_display()}',
        f'Trabajador: {worker.nombre}. Estado final: {worker.get_estado_display()}.'
    )


def cancelar_proceso(proceso, motivo_cancelacion=None):
    from django.utils import timezone
    worker = proceso.trabajador

    tareas_pendientes = proceso.tareas.exclude(
        estado__in=[Task.EstadoChoices.COMPLETADA,
                    Task.EstadoChoices.GESTIONADO_EXTERNO]
    )
    tareas_pendientes.update(estado=Task.EstadoChoices.ESCALADA)

    if proceso.tipo == Process.TipoChoices.CONTRATACION:
        worker.estado = Worker.EstadoChoices.ELIMINADO
    elif proceso.tipo in (Process.TipoChoices.CAMBIO_CECO,):
        worker.estado = Worker.EstadoChoices.ACTIVO
    elif proceso.tipo in (Process.TipoChoices.TERMINO,):
        worker.estado = Worker.EstadoChoices.ACTIVO
    elif proceso.tipo == Process.TipoChoices.DESPIDO:
        worker.estado = Worker.EstadoChoices.ACTIVO

    worker.save(update_fields=['estado'])

    proceso.estado = Process.EstadoChoices.CANCELADO
    proceso.fecha_cierre = timezone.now()
    if motivo_cancelacion:
        proceso.motivo = (proceso.motivo or '') + f' [CANCELADO: {motivo_cancelacion}]'
    proceso.save(update_fields=['estado', 'fecha_cierre', 'motivo'])

    _notificar_iniciador(
        proceso, 'proceso_cierre',
        f'Proceso cancelado: {proceso.get_tipo_display()}',
        f'Trabajador: {worker.nombre}. Motivo: {motivo_cancelacion or "No especificado"}.'
    )


def verificar_vencidas():
    from django.utils import timezone
    now = timezone.now()
    tareas_vencidas = Task.objects.filter(
        plazo_limite__lt=now,
        estado__in=[Task.EstadoChoices.PENDIENTE, Task.EstadoChoices.EN_PROCESO],
        omitida=False,
    )
    for task in tareas_vencidas:
        task.estado = Task.EstadoChoices.VENCIDA
        task.save(update_fields=['estado'])


def confirmar_cierre_despido(proceso):
    if proceso.tipo != Process.TipoChoices.DESPIDO:
        return
    _finalizar_proceso(proceso)
