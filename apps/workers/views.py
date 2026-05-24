from django.contrib import messages
from django.db import models as db_models
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, View

from apps.accounts.decorators import RoleRequiredMixin
from apps.notifications.services import notificar
from .models import Worker, CostCenterHistory


class WorkerListView(RoleRequiredMixin, ListView):
    model = Worker
    template_name = 'workers/worker_list.html'
    context_object_name = 'workers'
    roles_requeridos = ['administrador', 'rrhh', 'jefatura']
    paginate_by = 20

    def get_queryset(self):
        qs = Worker.objects.select_related('centro_costo_actual')

        user = self.request.user
        if user.roles.filter(nombre='jefatura').exists():
            cecos = user.cecos_a_cargo.filter(estado='activo')
            qs = qs.filter(centro_costo_actual__in=cecos)

        q = self.request.GET.get('q', '').strip()
        estado = self.request.GET.get('estado', '')
        ceco = self.request.GET.get('ceco', '')
        cargo = self.request.GET.get('cargo', '')

        if q:
            qs = qs.filter(
                db_models.Q(nombre__icontains=q) |
                db_models.Q(run__icontains=q)
            )
        if estado:
            qs = qs.filter(estado=estado)
        if ceco:
            qs = qs.filter(centro_costo_actual_id=ceco)
        if cargo:
            qs = qs.filter(cargo__icontains=cargo)

        if not self.request.GET.get('incluir_eliminados'):
            qs = qs.exclude(estado=Worker.EstadoChoices.ELIMINADO)

        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['query'] = self.request.GET.get('q', '')
        ctx['filtro_estado'] = self.request.GET.get('estado', '')
        ctx['filtro_ceco'] = self.request.GET.get('ceco', '')
        ctx['filtro_cargo'] = self.request.GET.get('cargo', '')
        ctx['incluir_eliminados'] = self.request.GET.get('incluir_eliminados', '')
        from apps.clients.models import CostCenter
        cecos_qs = CostCenter.objects.filter(estado='activo')
        if self.request.user.roles.filter(nombre='jefatura').exists():
            cecos_qs = cecos_qs.filter(jefatura=self.request.user)
        ctx['costcenters'] = cecos_qs
        return ctx


class WorkerDetailView(RoleRequiredMixin, DetailView):
    model = Worker
    template_name = 'workers/worker_detail.html'
    context_object_name = 'worker'
    roles_requeridos = ['administrador', 'rrhh', 'jefatura']

    def get_queryset(self):
        return Worker.objects.select_related('centro_costo_actual')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['historial_ceco'] = self.object.historial_ceco.select_related('centro_costo').all()
        return ctx


class WorkerCreateView(RoleRequiredMixin, CreateView):
    model = Worker
    template_name = 'workers/worker_form.html'
    fields = ['run', 'nombre', 'correo', 'cargo', 'fecha_ingreso_estimada', 'centro_costo_actual']
    roles_requeridos = ['administrador', 'rrhh', 'jefatura']
    success_url = reverse_lazy('workers:worker_list')

    def form_valid(self, form):
        messages.success(self.request, 'Trabajador registrado exitosamente.')
        return super().form_valid(form)


class WorkerUpdateView(RoleRequiredMixin, UpdateView):
    model = Worker
    template_name = 'workers/worker_form.html'
    fields = ['nombre', 'correo', 'cargo', 'fecha_ingreso_estimada', 'centro_costo_actual']
    roles_requeridos = ['administrador', 'rrhh', 'jefatura']
    success_url = reverse_lazy('workers:worker_list')

    def dispatch(self, request, *args, **kwargs):
        worker = self.get_object()
        if worker.estado in ('desvinculado', 'eliminado'):
            messages.error(request, 'No se puede editar un trabajador desvinculado o eliminado.')
            return redirect('workers:worker_detail', pk=worker.pk)
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        messages.success(self.request, 'Trabajador actualizado exitosamente.')
        return super().form_valid(form)


class WorkerDeleteView(RoleRequiredMixin, View):
    roles_requeridos = ['administrador', 'rrhh', 'jefatura']

    def post(self, request, pk):
        worker = get_object_or_404(Worker, pk=pk)
        if worker.estado != Worker.EstadoChoices.DESVINCULADO:
            messages.error(
                request,
                'Solo trabajadores desvinculados pueden ser eliminados lógicamente.'
            )
        else:
            worker.estado = Worker.EstadoChoices.ELIMINADO
            worker.save(update_fields=['estado'])
            messages.success(request, f'{worker.nombre} ha sido eliminado lógicamente.')
        return redirect('workers:worker_list')


class WorkerStateChangeView(RoleRequiredMixin, View):
    roles_requeridos = ['administrador', 'rrhh']

    def post(self, request, pk):
        worker = get_object_or_404(Worker, pk=pk)
        nuevo_estado = request.POST.get('estado', '')
        motivo = request.POST.get('motivo', '').strip()

        if nuevo_estado not in dict(Worker.EstadoChoices.choices):
            messages.error(request, 'Estado no válido.')
        elif not motivo:
            messages.error(request, 'Debes indicar un motivo para el cambio de estado manual.')
        else:
            old_state = worker.get_estado_display()
            worker.estado = nuevo_estado
            worker.save(update_fields=['estado'])
            notificar(
                usuario=request.user,
                tipo_evento='trabajador_cambio_estado_manual',
                titulo='Cambio de estado manual',
                descripcion=f'{worker.nombre}: {old_state} → {worker.get_estado_display()}. '
                            f'Motivo: {motivo}',
            )
            messages.success(
                request,
                f'Estado cambiado a {worker.get_estado_display()}.'
            )
        return redirect('workers:worker_detail', pk=pk)
