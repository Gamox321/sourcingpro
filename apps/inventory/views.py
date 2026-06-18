from django.contrib import messages
from django.db import models as db_models
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, View

from apps.accounts.decorators import RoleRequiredMixin
from .models import Asset, AssetType, AssetAssignment


ROLES_INVENTARIO = ['administrador', 'jefatura', 'logistica']


class AssetListView(RoleRequiredMixin, ListView):
    model = Asset
    template_name = 'inventory/asset_list.html'
    context_object_name = 'assets'
    roles_requeridos = ROLES_INVENTARIO + ['ti']
    paginate_by = 20

    def get_queryset(self):
        qs = Asset.objects.select_related('tipo')

        user = self.request.user
        if not user.roles.filter(nombre__in=ROLES_INVENTARIO).exists():
            if user.roles.filter(nombre='ti').exists():
                tipos_ti = AssetType.objects.filter(es_ti=True).values_list('pk', flat=True)
                qs = qs.filter(tipo__in=tipos_ti)
            elif user.roles.filter(nombre='prevencion').exists():
                tipos_epp = AssetType.objects.filter(es_prevencion=True).values_list('pk', flat=True)
                qs = qs.filter(tipo__in=tipos_epp)
            else:
                qs = qs.none()

        q = self.request.GET.get('q', '').strip()
        tipo = self.request.GET.get('tipo', '')
        estado = self.request.GET.get('estado', '')

        if q:
            qs = qs.filter(
                db_models.Q(codigo__icontains=q) |
                db_models.Q(nombre__icontains=q)
            )
        if tipo:
            qs = qs.filter(tipo_id=tipo)
        if estado:
            qs = qs.filter(estado=estado)

        if not self.request.GET.get('incluir_baja'):
            qs = qs.exclude(estado=Asset.EstadoChoices.DADO_DE_BAJA)

        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['query'] = self.request.GET.get('q', '')
        ctx['filtro_tipo'] = self.request.GET.get('tipo', '')
        ctx['filtro_estado'] = self.request.GET.get('estado', '')
        ctx['incluir_baja'] = self.request.GET.get('incluir_baja', '')
        ctx['tipos'] = AssetType.objects.filter(estado='activo')
        return ctx


class AssetDetailView(RoleRequiredMixin, DetailView):
    model = Asset
    template_name = 'inventory/asset_detail.html'
    context_object_name = 'asset'
    roles_requeridos = ROLES_INVENTARIO + ['ti', 'prevencion']

    def get_queryset(self):
        return Asset.objects.select_related('tipo')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['asignaciones'] = self.object.asignaciones.select_related('trabajador').all()
        from apps.workers.models import Worker
        ctx['trabajadores_disponibles'] = Worker.objects.filter(
            estado__in=['en_proceso', 'activo', 'en_transito']
        ).select_related('centro_costo_actual')
        return ctx


class AssetCreateView(RoleRequiredMixin, CreateView):
    model = Asset
    template_name = 'inventory/asset_form.html'
    fields = ['codigo', 'nombre', 'tipo', 'marca', 'modelo', 'numero_serie']
    roles_requeridos = ROLES_INVENTARIO
    success_url = reverse_lazy('inventory:asset_list')

    def form_valid(self, form):
        messages.success(self.request, 'Activo registrado exitosamente.')
        return super().form_valid(form)


class AssetUpdateView(RoleRequiredMixin, UpdateView):
    model = Asset
    template_name = 'inventory/asset_form.html'
    fields = ['codigo', 'nombre', 'tipo', 'marca', 'modelo', 'numero_serie']
    roles_requeridos = ROLES_INVENTARIO
    success_url = reverse_lazy('inventory:asset_list')

    def form_valid(self, form):
        messages.success(self.request, 'Activo actualizado exitosamente.')
        return super().form_valid(form)


class AssetAssignView(RoleRequiredMixin, View):
    roles_requeridos = ROLES_INVENTARIO + ['ti', 'prevencion']

    def post(self, request, pk):
        asset = get_object_or_404(Asset, pk=pk)

        if not request.user.roles.filter(nombre__in=ROLES_INVENTARIO).exists():
            roles_usuario = set(request.user.roles.values_list('nombre', flat=True))
            if 'ti' in roles_usuario and not asset.tipo.es_ti:
                messages.error(request, 'Solo puedes asignar activos gestionados por TI.')
                return redirect('inventory:asset_detail', pk=pk)
            if 'prevencion' in roles_usuario and not asset.tipo.es_prevencion:
                messages.error(request, 'Solo puedes asignar activos de EPP.')
                return redirect('inventory:asset_detail', pk=pk)

        worker_id = request.POST.get('trabajador', '').strip()

        if asset.estado != Asset.EstadoChoices.DISPONIBLE:
            messages.error(request, 'Solo activos disponibles pueden ser asignados.')
            return redirect('inventory:asset_detail', pk=pk)

        if not worker_id:
            messages.error(request, 'Debe seleccionar un trabajador.')
            return redirect('inventory:asset_detail', pk=pk)

        from apps.workers.models import Worker
        try:
            worker = Worker.objects.get(pk=worker_id)
        except Worker.DoesNotExist:
            messages.error(request, 'Trabajador no encontrado.')
            return redirect('inventory:asset_detail', pk=pk)

        AssetAssignment.objects.create(activo=asset, trabajador=worker)
        asset.cambiar_estado(Asset.EstadoChoices.ASIGNADO)

        messages.success(
            request,
            f'Activo {asset.codigo} asignado a {worker.nombre}.'
        )
        return redirect('inventory:asset_detail', pk=pk)


class AssetReturnView(RoleRequiredMixin, View):
    roles_requeridos = ROLES_INVENTARIO + ['ti', 'prevencion']

    def post(self, request, pk):
        asset = get_object_or_404(Asset, pk=pk)

        if not request.user.roles.filter(nombre__in=ROLES_INVENTARIO).exists():
            roles_usuario = set(request.user.roles.values_list('nombre', flat=True))
            if 'ti' in roles_usuario and not asset.tipo.es_ti:
                messages.error(request, 'Solo puedes gestionar devoluciones de activos gestionados por TI.')
                return redirect('inventory:asset_detail', pk=pk)
            if 'prevencion' in roles_usuario and not asset.tipo.es_prevencion:
                messages.error(request, 'Solo puedes gestionar devoluciones de activos de EPP.')
                return redirect('inventory:asset_detail', pk=pk)

        asignacion_id = request.POST.get('asignacion', '').strip()
        estado_dev = request.POST.get('estado_devolucion', '').strip()
        foto_evidencia = request.FILES.get('foto_evidencia')

        if not asignacion_id or not estado_dev:
            messages.error(request, 'Debe seleccionar la asignación y el estado de devolución.')
            return redirect('inventory:asset_detail', pk=pk)

        if estado_dev in ('danado', 'con_perdida') and not foto_evidencia:
            messages.error(request, 'Debe agregar foto como evidencia del daño/pérdida.')
            return redirect('inventory:asset_detail', pk=pk)

        try:
            asignacion = AssetAssignment.objects.get(
                pk=asignacion_id, activo=asset, fecha_devolucion__isnull=True
            )
        except AssetAssignment.DoesNotExist:
            messages.error(request, 'Asignación no encontrada o ya devuelta.')
            return redirect('inventory:asset_detail', pk=pk)

        from django.utils import timezone
        asignacion.fecha_devolucion = timezone.now()
        asignacion.estado_devolucion = estado_dev
        if foto_evidencia:
            asignacion.foto_evidencia = foto_evidencia
        asignacion.save(update_fields=['fecha_devolucion', 'estado_devolucion', 'foto_evidencia'])

        if asset.estado == Asset.EstadoChoices.ASIGNADO:
            asset.cambiar_estado(Asset.EstadoChoices.PENDIENTE_DEVOLUCION)

        if estado_dev == AssetAssignment.EstadoDevolucionChoices.BUENO:
            asset.cambiar_estado(Asset.EstadoChoices.DISPONIBLE)
        elif estado_dev == AssetAssignment.EstadoDevolucionChoices.DANADO:
            asset.cambiar_estado(Asset.EstadoChoices.EN_REVISION)

        messages.success(request, f'Devolución de {asset.codigo} registrada.')
        return redirect('inventory:asset_detail', pk=pk)


class AssetBajaView(RoleRequiredMixin, View):
    roles_requeridos = ['administrador', 'rrhh']

    def post(self, request, pk):
        asset = get_object_or_404(Asset, pk=pk)
        motivo = request.POST.get('motivo_baja', '').strip()

        if not motivo:
            messages.error(request, 'Debe indicar un motivo de baja.')
            return redirect('inventory:asset_detail', pk=pk)

        asset.motivo_baja = motivo
        asset.save(update_fields=['motivo_baja'])
        asset.cambiar_estado(Asset.EstadoChoices.DADO_DE_BAJA)

        messages.success(request, f'Activo {asset.codigo} dado de baja.')
        return redirect('inventory:asset_detail', pk=pk)
