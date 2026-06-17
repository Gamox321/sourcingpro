from django.contrib import messages
from django.db import models as db_models
from django.shortcuts import redirect, get_object_or_404
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.generic import ListView, DetailView, TemplateView, View
from django.utils.decorators import method_decorator

from apps.accounts.decorators import RoleRequiredMixin
from apps.inventory.models import Asset, AssetType
from apps.workers.models import Worker
from .models import Process, Task
from .forms import (
    ContratacionForm, CambioCeCoForm, TerminoForm, DespidoForm,
    AsignacionActivosForm,
)
from . import services


ROLES_PROCESOS = ['administrador', 'rrhh']


def _get_user_cecos(user):
    if user.roles.filter(nombre__in=['administrador', 'rrhh']).exists():
        return None
    if user.roles.filter(nombre='jefatura').exists():
        return user.cecos_a_cargo.filter(estado='activo')
    return None


class ProcessTypeSelectView(RoleRequiredMixin, TemplateView):
    template_name = 'processes/process_type_select.html'
    roles_requeridos = ROLES_PROCESOS


class ProcessCreateContratacionView(RoleRequiredMixin, TemplateView):
    template_name = 'processes/process_form.html'
    roles_requeridos = ROLES_PROCESOS

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['form'] = ContratacionForm(user_cecos=_get_user_cecos(self.request.user))
        ctx['tipo'] = 'contratacion'
        ctx['titulo'] = 'Nueva Contratacion'
        ctx['descripcion'] = 'Registra un nuevo trabajador e inicia el proceso de contratacion con todas las areas involucradas.'
        ctx['tareas_info'] = [
            ('Creacion cuenta TI', 'TI'),
            ('Examenes preocupacionales', 'Prevencion'),
            ('Induccion y EPP', 'Prevencion'),
            ('Equipamiento', 'Logistica'),
        ]
        return ctx

    def post(self, request):
        form = ContratacionForm(request.POST, user_cecos=_get_user_cecos(request.user))
        if form.is_valid():
            try:
                proceso = services.crear_proceso_contratacion(
                    usuario=request.user,
                    datos_worker=form.cleaned_data,
                )
                messages.success(request, 'Proceso de contratacion iniciado exitosamente.')
                return redirect('processes:process_detail', pk=proceso.pk)
            except Exception as e:
                messages.error(request, f'Error al crear el proceso: {e}')
        ctx = self.get_context_data()
        ctx['form'] = form
        return self.render_to_response(ctx)


class ProcessCreateCambioCeCoView(RoleRequiredMixin, TemplateView):
    template_name = 'processes/process_form.html'
    roles_requeridos = ROLES_PROCESOS

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['form'] = CambioCeCoForm(user_cecos=_get_user_cecos(self.request.user))
        ctx['tipo'] = 'cambio_ceco'
        ctx['titulo'] = 'Nuevo Cambio de Centro de Costo'
        ctx['descripcion'] = 'Transfere un trabajador activo de un centro de costo a otro, gestionando devolucion de activos y reasignacion.'
        ctx['tareas_info'] = [
            ('Fase 1: Devolucion de activos (si tiene)', 'Logistica'),
            ('Fase 2: Creacion cuenta TI', 'TI'),
            ('Fase 2: Induccion y EPP', 'Prevencion'),
            ('Fase 2: Equipamiento', 'Logistica'),
        ]
        return ctx

    def post(self, request):
        form = CambioCeCoForm(request.POST, user_cecos=_get_user_cecos(request.user))
        if form.is_valid():
            try:
                proceso = services.crear_proceso_cambio_ceco(
                    usuario=request.user,
                    worker_id=form.cleaned_data['trabajador'].pk,
                    ceco_destino_id=form.cleaned_data['ceco_destino'].pk,
                    fecha=form.cleaned_data['fecha_estimada'],
                    motivo=form.cleaned_data['motivo'],
                )
                messages.success(request, 'Cambio de centro de costo iniciado.')
                return redirect('processes:process_detail', pk=proceso.pk)
            except Exception as e:
                messages.error(request, f'Error: {e}')
        ctx = self.get_context_data()
        ctx['form'] = form
        return self.render_to_response(ctx)


class ProcessCreateTerminoView(RoleRequiredMixin, TemplateView):
    template_name = 'processes/process_form.html'
    roles_requeridos = ROLES_PROCESOS

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['form'] = TerminoForm(user_cecos=_get_user_cecos(self.request.user))
        ctx['tipo'] = 'termino'
        ctx['titulo'] = 'Nuevo Termino de Contrato'
        ctx['descripcion'] = 'Gestiona la salida programada de un trabajador: devolucion de activos, finiquito y bloqueo de accesos.'
        ctx['tareas_info'] = [
            ('Devolucion de activos', 'Logistica'),
            ('Preparar bloqueo accesos', 'TI'),
            ('Coordinacion finiquito', 'Finanzas'),
            ('Bloqueo de accesos', 'TI'),
        ]
        return ctx

    def post(self, request):
        form = TerminoForm(request.POST, user_cecos=_get_user_cecos(request.user))
        if form.is_valid():
            try:
                proceso = services.crear_proceso_termino(
                    usuario=request.user,
                    worker_id=form.cleaned_data['trabajador'].pk,
                    fecha_termino=form.cleaned_data['fecha_termino'],
                    motivo=form.cleaned_data['motivo'],
                )
                messages.success(request, 'Proceso de termino iniciado.')
                return redirect('processes:process_detail', pk=proceso.pk)
            except Exception as e:
                messages.error(request, f'Error: {e}')
        ctx = self.get_context_data()
        ctx['form'] = form
        return self.render_to_response(ctx)


class ProcessCreateDespidoView(RoleRequiredMixin, TemplateView):
    template_name = 'processes/process_form.html'
    roles_requeridos = ROLES_PROCESOS

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['form'] = DespidoForm(user_cecos=_get_user_cecos(self.request.user))
        ctx['tipo'] = 'despido'
        ctx['titulo'] = 'Nuevo Despido'
        ctx['descripcion'] = 'Inicia un proceso de despido con bloqueo inmediato de accesos, recuperacion de activos y finiquito. Requiere confirmacion RRHH.'
        ctx['tareas_info'] = [
            ('Recuperacion de activos', 'Logistica'),
            ('Bloqueo de accesos (CRITICO)', 'TI'),
            ('Coordinacion finiquito', 'Finanzas'),
        ]
        return ctx

    def post(self, request):
        form = DespidoForm(request.POST, user_cecos=_get_user_cecos(request.user))
        if form.is_valid():
            try:
                proceso = services.crear_proceso_despido(
                    usuario=request.user,
                    worker_id=form.cleaned_data['trabajador'].pk,
                    fecha=form.cleaned_data['fecha_efectiva'],
                    motivo=form.cleaned_data['motivo'],
                    causal_legal=form.cleaned_data['causal_legal'],
                )
                messages.success(request, 'Proceso de despido iniciado.')
                return redirect('processes:process_detail', pk=proceso.pk)
            except Exception as e:
                messages.error(request, f'Error: {e}')
        ctx = self.get_context_data()
        ctx['form'] = form
        return self.render_to_response(ctx)


class ProcessCreateAsignacionActivosView(RoleRequiredMixin, TemplateView):
    template_name = 'processes/process_form.html'
    roles_requeridos = ROLES_PROCESOS

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['form'] = AsignacionActivosForm(user_cecos=_get_user_cecos(self.request.user))
        ctx['tipo'] = 'asignacion_activos'
        ctx['titulo'] = 'Asignacion de Activos TI'
        ctx['descripcion'] = 'Solicita la asignacion de equipo TI a un trabajador activo. El area de TI seleccionara y asignara el equipo correspondiente.'
        ctx['tareas_info'] = [
            ('Asignacion de Equipo TI', 'TI'),
        ]
        return ctx

    def post(self, request):
        form = AsignacionActivosForm(request.POST, user_cecos=_get_user_cecos(request.user))
        if form.is_valid():
            try:
                proceso = services.crear_proceso_asignacion_activos(
                    usuario=request.user,
                    worker_id=form.cleaned_data['trabajador'].pk,
                    comentario=form.cleaned_data.get('comentario', ''),
                )
                messages.success(request, 'Proceso de asignacion de activos iniciado.')
                return redirect('processes:process_detail', pk=proceso.pk)
            except Exception as e:
                messages.error(request, f'Error: {e}')
        ctx = self.get_context_data()
        ctx['form'] = form
        return self.render_to_response(ctx)


class ProcessListView(RoleRequiredMixin, ListView):
    model = Process
    template_name = 'processes/process_list.html'
    context_object_name = 'processes'
    roles_requeridos = ROLES_PROCESOS + ['ti', 'prevencion', 'finanzas', 'logistica']
    paginate_by = 20

    def get_queryset(self):
        qs = Process.objects.select_related(
            'trabajador', 'usuario_inicio', 'ceco_origen', 'ceco_destino'
        )

        user = self.request.user
        if user.roles.filter(nombre='jefatura').exists():
            cecos = user.cecos_a_cargo.filter(estado='activo')
            qs = qs.filter(
                db_models.Q(trabajador__centro_costo_actual__in=cecos) |
                db_models.Q(ceco_origen__in=cecos) |
                db_models.Q(ceco_destino__in=cecos)
            )

        tipo = self.request.GET.get('tipo', '')
        estado = self.request.GET.get('estado', '')
        if tipo:
            qs = qs.filter(tipo=tipo)
        if estado:
            qs = qs.filter(estado=estado)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['filtro_tipo'] = self.request.GET.get('tipo', '')
        ctx['filtro_estado'] = self.request.GET.get('estado', '')
        return ctx


class ProcessDetailView(RoleRequiredMixin, DetailView):
    model = Process
    template_name = 'processes/process_detail.html'
    context_object_name = 'process'
    roles_requeridos = ROLES_PROCESOS + ['ti', 'prevencion', 'finanzas', 'logistica']

    @method_decorator(never_cache)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def get_queryset(self):
        qs = Process.objects.select_related(
            'trabajador', 'usuario_inicio', 'ceco_origen', 'ceco_destino'
        )
        user = self.request.user
        if user.roles.filter(nombre='jefatura').exists():
            cecos = user.cecos_a_cargo.filter(estado='activo')
            qs = qs.filter(
                db_models.Q(trabajador__centro_costo_actual__in=cecos) |
                db_models.Q(ceco_origen__in=cecos) |
                db_models.Q(ceco_destino__in=cecos)
            )
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        tareas = self.object.tareas.select_related('usuario_responsable').all()
        ctx['tareas'] = tareas
        
        completadas = sum(
            1 for t in tareas
            if t.estado in (Task.EstadoChoices.COMPLETADA, Task.EstadoChoices.GESTIONADO_EXTERNO)
        )
        total = tareas.count()
        ctx['tareas_completadas_count'] = completadas
        ctx['porcentaje_completado'] = int(completadas / total * 100) if total > 0 else 0
        
        for t in tareas:
            t.esta_bloqueada = t.tareas_anteriores().exists()
        
        return ctx


class ProcessCloseView(RoleRequiredMixin, View):
    roles_requeridos = ['administrador', 'rrhh']

    def post(self, request, pk):
        proceso = get_object_or_404(Process, pk=pk)
        accion = request.POST.get('accion', '')

        if accion == 'completar':
            if proceso.requiere_confirmacion_rrhh:
                services.confirmar_cierre_despido(proceso)
            else:
                services.finalizar_proceso_manual(proceso)
            messages.success(request, 'Proceso cerrado exitosamente.')

        elif accion == 'cancelar':
            motivo = request.POST.get('motivo_cancelacion', '')
            services.cancelar_proceso(proceso, motivo)
            messages.success(request, 'Proceso cancelado.')

        return redirect('processes:process_detail', pk=pk)


class TaskCompleteView(RoleRequiredMixin, View):
    roles_requeridos = ROLES_PROCESOS + ['ti', 'prevencion', 'finanzas', 'logistica']

    def post(self, request, pk, task_pk):
        task = get_object_or_404(Task, pk=task_pk, proceso_id=pk)

        if task.estado in (Task.EstadoChoices.COMPLETADA, Task.EstadoChoices.GESTIONADO_EXTERNO):
            messages.warning(request, 'Esta tarea ya fue completada.')
            return redirect('processes:process_detail', pk=pk)

        es_responsable = task.usuario_responsable == request.user
        es_admin = request.user.roles.filter(nombre='administrador').exists()
        if not (es_responsable or es_admin):
            messages.error(request, 'No tienes permiso para completar esta tarea.')
            return redirect('processes:process_detail', pk=pk)

        anteriores = task.tareas_anteriores()
        if anteriores.exists():
            names = ', '.join([t.get_tipo_display() for t in anteriores])
            messages.error(
                request,
                f'No puede completar esta tarea. Primero complete: {names}.'
            )
            return redirect('processes:process_detail', pk=pk)

        # BLOQUEO_ACCESOS en TERMINO requiere FINIQUITO_COORDINACION completado
        if (task.tipo == Task.TipoChoices.BLOQUEO_ACCESOS
                and task.proceso.tipo == Process.TipoChoices.TERMINO):
            finiquito = task.proceso.tareas.filter(
                tipo=Task.TipoChoices.FINIQUITO_COORDINACION
            ).first()
            if finiquito and finiquito.estado != Task.EstadoChoices.COMPLETADA:
                messages.error(
                    request,
                    'No puede bloquear accesos hasta que Finanzas complete la coordinación de finiquito. '
                    f'<a href="mailto:?subject=Recordatorio: Finiquito proceso #{task.proceso.pk}" class="alert-link">Enviar recordatorio a Finanzas</a>'
                )
                return redirect('processes:process_detail', pk=pk)

        if task.tipo in (Task.TipoChoices.FINIQUITO_COORDINACION,):
            services.gestionar_externamente_tarea(task)
            messages.success(request, f'Tarea {task.get_tipo_display()} marcada como gestionada externamente.')
        else:
            services.completar_tarea(task)
            messages.success(request, f'Tarea {task.get_tipo_display()} completada.')

        return redirect('processes:process_detail', pk=pk)


class TaskAccountCreateView(RoleRequiredMixin, TemplateView):
    template_name = 'processes/task_account_create.html'
    roles_requeridos = ROLES_PROCESOS + ['ti', 'prevencion', 'finanzas', 'logistica']

    def dispatch(self, request, *args, **kwargs):
        self.task = get_object_or_404(
            Task.objects.select_related('proceso__trabajador', 'usuario_responsable'),
            pk=kwargs['task_pk'],
            proceso_id=kwargs['pk'],
        )
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['task'] = self.task
        ctx['process'] = self.task.proceso
        ctx['worker'] = self.task.proceso.trabajador
        return ctx

    def post(self, request, pk, task_pk):
        task = self.task

        if task.estado in (Task.EstadoChoices.COMPLETADA, Task.EstadoChoices.GESTIONADO_EXTERNO):
            messages.warning(request, 'Esta tarea ya fue completada.')
            return redirect('processes:process_detail', pk=pk)

        es_responsable = task.usuario_responsable == request.user
        es_admin = request.user.roles.filter(nombre='administrador').exists()
        if not (es_responsable or es_admin):
            messages.error(request, 'No tienes permiso para completar esta tarea.')
            return redirect('processes:process_detail', pk=pk)

        anteriores = task.tareas_anteriores()
        if anteriores.exists():
            names = ', '.join([t.get_tipo_display() for t in anteriores])
            messages.error(request, f'No puede completar esta tarea. Primero complete: {names}.')
            return redirect('processes:process_detail', pk=pk)

        if task.tipo != Task.TipoChoices.CREAR_CUENTA_TI:
            messages.error(request, 'Esta tarea no es de creacion de cuenta TI.')
            return redirect('processes:process_detail', pk=pk)

        worker = task.proceso.trabajador
        email = request.POST.get('email', '').strip()
        clave = request.POST.get('clave', '').strip()
        notas = request.POST.get('notas', '').strip()

        if email:
            worker.cuenta_ti_email = email
            worker.cuenta_ti_clave_inicial = clave or worker.cuenta_ti_clave_inicial
            worker.cuenta_ti_fecha_creacion = timezone.now()
            worker.cuenta_ti_notas = notas or worker.cuenta_ti_notas
            worker.save(update_fields=[
                'cuenta_ti_email', 'cuenta_ti_clave_inicial',
                'cuenta_ti_fecha_creacion', 'cuenta_ti_notas',
            ])

        services.completar_tarea(task)

        if email:
            messages.success(request, f'Cuenta TI registrada para {worker.nombre} ({email}). Tarea completada.')
        else:
            messages.success(request, f'Tarea completada (sin registrar credenciales).')

        return redirect('processes:process_detail', pk=pk)


class TaskAssetAssignView(RoleRequiredMixin, TemplateView):
    template_name = 'processes/task_asset_assign.html'
    roles_requeridos = ROLES_PROCESOS + ['ti', 'prevencion', 'finanzas', 'logistica']

    def dispatch(self, request, *args, **kwargs):
        self.task = get_object_or_404(
            Task.objects.select_related('proceso__trabajador', 'usuario_responsable'),
            pk=kwargs['task_pk'],
            proceso_id=kwargs['pk'],
        )
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['task'] = self.task
        ctx['process'] = self.task.proceso
        ctx['worker'] = self.task.proceso.trabajador

        if self.task.tipo == Task.TipoChoices.EPP_INDUCCION:
            ctx['asset_label'] = 'EPP'
            ctx['available_assets'] = Asset.objects.filter(
                tipo__es_prevencion=True,
                estado=Asset.EstadoChoices.DISPONIBLE,
            ).select_related('tipo').order_by('tipo__nombre', 'codigo')
        elif self.task.tipo in (Task.TipoChoices.EQUIPAMIENTO, Task.TipoChoices.ASIGNAR_EQUIPO_TI):
            ctx['asset_label'] = 'Equipo TI'
            ctx['available_assets'] = Asset.objects.filter(
                tipo__es_ti=True,
                estado=Asset.EstadoChoices.DISPONIBLE,
            ).select_related('tipo').order_by('tipo__nombre', 'codigo')
        else:
            ctx['asset_label'] = 'Activo'
            ctx['available_assets'] = Asset.objects.none()

        return ctx

    def post(self, request, pk, task_pk):
        task = self.task

        if task.estado in (Task.EstadoChoices.COMPLETADA, Task.EstadoChoices.GESTIONADO_EXTERNO):
            messages.warning(request, 'Esta tarea ya fue completada.')
            return redirect('processes:process_detail', pk=pk)

        es_responsable = task.usuario_responsable == request.user
        es_admin = request.user.roles.filter(nombre='administrador').exists()
        if not (es_responsable or es_admin):
            messages.error(request, 'No tienes permiso para completar esta tarea.')
            return redirect('processes:process_detail', pk=pk)

        anteriores = task.tareas_anteriores()
        if anteriores.exists():
            names = ', '.join([t.get_tipo_display() for t in anteriores])
            messages.error(request, f'No puede completar esta tarea. Primero complete: {names}.')
            return redirect('processes:process_detail', pk=pk)

        asset_ids = request.POST.getlist('activos', [])
        if asset_ids:
            assigned = services.completar_tarea_con_activos(task, asset_ids)
            if assigned:
                messages.success(
                    request,
                    f'Tarea completada. {len(assigned)} activos asignados: {", ".join(assigned)}.'
                )
            else:
                messages.success(request, f'Tarea completada (sin activos asignados).')
        else:
            services.completar_tarea(task)
            messages.success(request, f'Tarea {task.get_tipo_display()} completada (sin asignar activos).')

        return redirect('processes:process_detail', pk=pk)
