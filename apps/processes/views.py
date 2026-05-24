from django.contrib import messages
from django.db import models as db_models
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, TemplateView, View

from apps.accounts.decorators import RoleRequiredMixin
from .models import Process, Task
from .forms import (
    ContratacionForm, CambioCeCoForm, TerminoForm, DespidoForm,
)
from . import services


ROLES_PROCESOS = ['administrador', 'rrhh', 'jefatura']


class ProcessTypeSelectView(RoleRequiredMixin, TemplateView):
    template_name = 'processes/process_type_select.html'
    roles_requeridos = ROLES_PROCESOS


class ProcessCreateContratacionView(RoleRequiredMixin, TemplateView):
    template_name = 'processes/process_form.html'
    roles_requeridos = ROLES_PROCESOS

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['form'] = ContratacionForm()
        ctx['tipo'] = 'contratacion'
        ctx['titulo'] = 'Nueva Contratación'
        return ctx

    def post(self, request):
        form = ContratacionForm(request.POST)
        if form.is_valid():
            try:
                proceso = services.crear_proceso_contratacion(
                    usuario=request.user,
                    datos_worker=form.cleaned_data,
                )
                messages.success(request, 'Proceso de contratación iniciado exitosamente.')
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
        ctx['form'] = CambioCeCoForm()
        ctx['tipo'] = 'cambio_ceco'
        ctx['titulo'] = 'Nuevo Cambio de Centro de Costo'
        return ctx

    def post(self, request):
        form = CambioCeCoForm(request.POST)
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
        ctx['form'] = TerminoForm()
        ctx['tipo'] = 'termino'
        ctx['titulo'] = 'Nuevo Término de Contrato'
        return ctx

    def post(self, request):
        form = TerminoForm(request.POST)
        if form.is_valid():
            try:
                proceso = services.crear_proceso_termino(
                    usuario=request.user,
                    worker_id=form.cleaned_data['trabajador'].pk,
                    fecha_termino=form.cleaned_data['fecha_termino'],
                    motivo=form.cleaned_data['motivo'],
                )
                messages.success(request, 'Proceso de término iniciado.')
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
        ctx['form'] = DespidoForm()
        ctx['tipo'] = 'despido'
        ctx['titulo'] = 'Nuevo Despido'
        return ctx

    def post(self, request):
        form = DespidoForm(request.POST)
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
        ctx['tareas'] = self.object.tareas.select_related('usuario_responsable').all()
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

        if task.tipo in (Task.TipoChoices.FINIQUITO_COORDINACION,):
            services.gestionar_externamente_tarea(task)
            messages.success(request, f'Tarea {task.get_tipo_display()} marcada como gestionada externamente.')
        else:
            services.completar_tarea(task)
            messages.success(request, f'Tarea {task.get_tipo_display()} completada.')

        return redirect('processes:process_detail', pk=pk)
