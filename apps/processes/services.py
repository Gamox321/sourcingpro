import datetime

from django.db import transaction
from django.utils import timezone

from apps.accounts.models import User, Role
from apps.workers.models import Worker, CostCenterHistory
from apps.inventory.models import Asset, AssetAssignment
from .models import Process, Task


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


TASK_TYPE_ROLE_MAP = {
    Task.TipoChoices.CREAR_CUENTA_TI: 'ti',
    Task.TipoChoices.EXAMENES_PREOCUPACIONALES: 'prevencion',
    Task.TipoChoices.EPP_INDUCCION: 'prevencion',
    Task.TipoChoices.EQUIPAMIENTO: 'logistica',
    Task.TipoChoices.DEVOLUCION_ACTIVOS: 'logistica',
    Task.TipoChoices.RECUPERACION_ACTIVOS: 'logistica',
    Task.TipoChoices.PREPARAR_BLOQUEO_ACCESOS: 'ti',
    Task.TipoChoices.BLOQUEO_ACCESOS: 'ti',
    Task.TipoChoices.FINIQUITO_COORDINACION: 'finanzas',
}


def _find_user_for_role(role_name):
    user = User.objects.filter(
        is_active=True, roles__nombre=role_name
    ).distinct().first()
    if user:
        return user
    return User.objects.filter(is_active=True).distinct().first()


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
                 plazo_limite=None, omitida=False, motivo_omision=None):
    role_name = TASK_TYPE_ROLE_MAP.get(tipo)
    responsable = _find_user_for_role(role_name) if role_name else None

    return Task.objects.create(
        proceso=proceso,
        tipo=tipo,
        urgencia=urgencia,
        descripcion=descripcion,
        plazo_limite=_make_aware(plazo_limite),
        omitida=omitida,
        motivo_omision=motivo_omision,
        usuario_responsable=responsable,
    )


@transaction.atomic
def crear_proceso_contratacion(usuario, datos_worker):
    from apps.clients.models import CostCenter
    ceco = CostCenter.objects.get(pk=datos_worker['centro_costo'])

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

    _create_task(proceso, Task.TipoChoices.CREAR_CUENTA_TI,
                 'Crear cuenta corporativa y accesos según cargo.')
    _create_task(proceso, Task.TipoChoices.EXAMENES_PREOCUPACIONALES,
                 'Gestionar exámenes pre-ocupacionales.')
    _create_task(proceso, Task.TipoChoices.EPP_INDUCCION,
                 'Entregar EPP y realizar inducción.')
    _create_task(proceso, Task.TipoChoices.EQUIPAMIENTO,
                 'Entregar equipamiento según cargo.',)

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
            tipo=epp_type, estado='disponible'
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
    worker = proceso.trabajador
    ceco_destino = proceso.ceco_destino
    fecha = timezone.now()

    CostCenterHistory.objects.create(
        trabajador=worker,
        centro_costo=ceco_destino,
        fecha_inicio=fecha.date(),
        proceso=proceso,
    )

    _generar_reincorporacion_cambio_ceco(proceso, worker, ceco_destino, fecha)


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
                 plazo_limite=fecha_termino)
    _create_task(proceso, Task.TipoChoices.PREPARAR_BLOQUEO_ACCESOS,
                 'Preparar bloqueo de cuenta y accesos para fecha de término.',
                 plazo_limite=fecha_termino)
    _create_task(proceso, Task.TipoChoices.FINIQUITO_COORDINACION,
                 'Coordinar finiquito en sistema externo.',
                 plazo_limite=fecha_termino)

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

    _create_task(proceso, Task.TipoChoices.BLOQUEO_ACCESOS,
                 'BLOQUEO INMEDIATO de accesos y cuentas.',
                 urgencia=Task.UrgenciaChoices.CRITICA)
    _create_task(proceso, Task.TipoChoices.RECUPERACION_ACTIVOS,
                 'Recuperar todos los activos asignados al trabajador.',
                 plazo_limite=fecha)
    _create_task(proceso, Task.TipoChoices.FINIQUITO_COORDINACION,
                 'Coordinar finiquito y descuentos en sistema externo.',
                 plazo_limite=fecha)

    asignaciones = AssetAssignment.objects.filter(
        trabajador=worker, fecha_devolucion__isnull=True
    ).select_related('activo')
    for aa in asignaciones:
        aa.activo.cambiar_estado(Asset.EstadoChoices.PENDIENTE_DEVOLUCION)

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
    task.estado = Task.EstadoChoices.COMPLETADA
    task.fecha_completado = timezone.now()
    task.save(update_fields=['estado', 'fecha_completado'])

    _notificar_iniciador(
        task.proceso, 'tarea_cambio_estado',
        f'Tarea completada: {task.get_tipo_display()}',
        f'Trabajador: {task.proceso.trabajador.nombre}. Proceso #{task.proceso.pk}'
    )

    _check_process_completion(task.proceso)
    return task


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
