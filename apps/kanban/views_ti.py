from datetime import timedelta

from django.contrib import messages
from django.db import models as db_models
from django.db.models import Count, Q
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import TemplateView, ListView, CreateView, View

from apps.accounts.decorators import RoleRequiredMixin
from apps.inventory.models import Asset, AssetType
from apps.processes.models import Process, Task


TI_TASK_TYPES = [
    Task.TipoChoices.CREAR_CUENTA_TI,
    Task.TipoChoices.PREPARAR_BLOQUEO_ACCESOS,
    Task.TipoChoices.BLOQUEO_ACCESOS,
]


class TIDashboardView(RoleRequiredMixin, TemplateView):
    template_name = 'ti/dashboard.html'
    roles_requeridos = ['ti']

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        
        now = timezone.now()
        
        mis_tareas = Task.objects.filter(
            usuario_responsable=self.request.user,
            tipo__in=TI_TASK_TYPES,
            omitida=False,
            proceso__estado=Process.EstadoChoices.EN_CURSO,
        ).select_related('proceso__trabajador', 'proceso__ceco_origen', 'proceso__ceco_destino')
        
        tareas_pendientes = mis_tareas.filter(
            estado__in=[Task.EstadoChoices.PENDIENTE, Task.EstadoChoices.EN_PROCESO]
        )
        
        primer_dia_mes = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        tareas_completadas_mes = Task.objects.filter(
            usuario_responsable=self.request.user,
            tipo__in=TI_TASK_TYPES,
            estado=Task.EstadoChoices.COMPLETADA,
            fecha_completado__gte=primer_dia_mes,
        ).count()
        
        try:
            tipo_equipo_ti = AssetType.objects.get(nombre__icontains='Equipo TI')
            equipos_ti_total = Asset.objects.filter(tipo=tipo_equipo_ti).count()
            equipos_ti_asignados = Asset.objects.filter(
                tipo=tipo_equipo_ti,
                estado=Asset.EstadoChoices.ASIGNADO
            ).count()
        except AssetType.DoesNotExist:
            equipos_ti_total = 0
            equipos_ti_asignados = 0
        
        alerta_critica = mis_tareas.filter(
            urgencia=Task.UrgenciaChoices.CRITICA,
            estado__in=[Task.EstadoChoices.PENDIENTE, Task.EstadoChoices.EN_PROCESO],
        ).first()
        
        ctx['stats'] = {
            'tareas_pendientes': tareas_pendientes.count(),
            'tareas_criticas': mis_tareas.filter(
                urgencia=Task.UrgenciaChoices.CRITICA,
                estado__in=[Task.EstadoChoices.PENDIENTE, Task.EstadoChoices.EN_PROCESO],
            ).count(),
            'equipos_ti_asignados': equipos_ti_asignados,
            'equipos_ti_total': equipos_ti_total,
            'tareas_completadas_mes': tareas_completadas_mes,
        }
        
        ctx['alerta_critica'] = alerta_critica
        ctx['mis_tareas'] = tareas_pendientes.order_by('-urgencia', 'plazo_limite')[:10]
        
        try:
            tipo_equipo_ti = AssetType.objects.get(nombre__icontains='Equipo TI')
            inventario_ti = Asset.objects.filter(
                tipo=tipo_equipo_ti
            ).select_related('tipo').prefetch_related('asignaciones__trabajador')[:10]
        except AssetType.DoesNotExist:
            inventario_ti = Asset.objects.none()
        
        ctx['inventario_ti'] = inventario_ti
        
        return ctx


class TIInventarioView(RoleRequiredMixin, ListView):
    model = Asset
    template_name = 'ti/inventario.html'
    context_object_name = 'assets'
    roles_requeridos = ['ti']
    paginate_by = 20

    def get_queryset(self):
        try:
            tipo_equipo_ti = AssetType.objects.get(nombre__icontains='Equipo TI')
            qs = Asset.objects.filter(tipo=tipo_equipo_ti).select_related('tipo')
        except AssetType.DoesNotExist:
            qs = Asset.objects.none()

        q = self.request.GET.get('q', '').strip()
        estado = self.request.GET.get('estado', '')

        if q:
            qs = qs.filter(
                db_models.Q(codigo__icontains=q) |
                db_models.Q(nombre__icontains=q)
            )
        if estado:
            qs = qs.filter(estado=estado)

        if not self.request.GET.get('incluir_baja'):
            qs = qs.exclude(estado=Asset.EstadoChoices.DADO_DE_BAJA)

        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['query'] = self.request.GET.get('q', '')
        ctx['filtro_estado'] = self.request.GET.get('estado', '')
        ctx['incluir_baja'] = self.request.GET.get('incluir_baja', '')
        return ctx


class TITableroGeneralView(RoleRequiredMixin, TemplateView):
    template_name = 'ti/tablero.html'
    roles_requeridos = ['ti']

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        
        qs = Task.objects.filter(
            tipo__in=TI_TASK_TYPES,
            omitida=False,
            proceso__estado=Process.EstadoChoices.EN_CURSO,
        ).select_related('proceso__trabajador', 'usuario_responsable')
        
        ctx['pendientes'] = qs.filter(estado=Task.EstadoChoices.PENDIENTE)
        ctx['en_proceso'] = qs.filter(estado=Task.EstadoChoices.EN_PROCESO)
        ctx['completadas'] = qs.filter(
            estado__in=[Task.EstadoChoices.COMPLETADA, Task.EstadoChoices.GESTIONADO_EXTERNO]
        )
        
        return ctx


class TIAssetCreateView(RoleRequiredMixin, CreateView):
    model = Asset
    template_name = 'ti/asset_form.html'
    fields = ['codigo', 'nombre']
    roles_requeridos = ['ti']
    success_url = reverse_lazy('ti:inventario')

    def form_valid(self, form):
        try:
            tipo_equipo_ti = AssetType.objects.get(nombre__icontains='Equipo TI')
        except AssetType.DoesNotExist:
            messages.error(self.request, 'No existe el tipo de activo "Equipo TI".')
            return redirect('ti:inventario')
        
        form.instance.tipo = tipo_equipo_ti
        form.instance.estado = Asset.EstadoChoices.DISPONIBLE
        messages.success(self.request, f'Equipo TI "{form.instance.nombre}" creado exitosamente.')
        return super().form_valid(form)


class TIBloqueoUrgenteView(RoleRequiredMixin, TemplateView):
    """
    RF-29: UI de bloqueo inmediato para despido.
    Muestra lista de bloqueos urgentes pendientes y permite confirmar bloqueo ejecutado.
    """
    template_name = 'ti/bloqueo_urgente.html'
    roles_requeridos = ['ti']

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        
        # Tareas de bloqueo urgente (despido) pendientes
        bloqueos_urgentes = Task.objects.filter(
            tipo=Task.TipoChoices.BLOQUEO_ACCESOS,
            urgencia=Task.UrgenciaChoices.CRITICA,
            estado__in=[Task.EstadoChoices.PENDIENTE, Task.EstadoChoices.EN_PROCESO],
            proceso__tipo=Process.TipoChoices.DESPIDO,
            proceso__estado=Process.EstadoChoices.EN_CURSO,
        ).select_related('proceso__trabajador', 'usuario_responsable').order_by('proceso__fecha_inicio')
        
        ctx['bloqueos_urgentes'] = bloqueos_urgentes
        ctx['total_urgentes'] = bloqueos_urgentes.count()
        
        return ctx


class TIConfirmarBloqueoView(RoleRequiredMixin, View):
    """
    RF-29: Confirma que el bloqueo de accesos fue ejecutado efectivamente.
    """
    roles_requeridos = ['ti']

    def post(self, request, pk):
        task = get_object_or_404(
            Task, 
            pk=pk, 
            tipo=Task.TipoChoices.BLOQUEO_ACCESOS,
            proceso__tipo=Process.TipoChoices.DESPIDO,
        )
        
        confirmacion = request.POST.get('confirmacion', '')
        
        if not confirmacion:
            messages.error(request, 'Debe ingresar una confirmación del bloqueo.')
            return redirect('ti:bloqueo_urgente')
        
        # Marcar tarea como completada
        task.estado = Task.EstadoChoices.COMPLETADA
        task.fecha_completado = timezone.now()
        task.descripcion = f"{task.descripcion or ''}\n\n[CONFIRMACIÓN BLOQUEO]: {confirmacion}"
        task.save(update_fields=['estado', 'fecha_completado', 'descripcion'])
        
        # Notificar a RRHH que el bloqueo fue ejecutado (RF-36)
        from apps.notifications.services import notificar
        notificar(
            usuario=task.proceso.usuario_inicio,
            tipo_evento='bloqueo_ejecutado',
            titulo=f'Bloqueo Ejecutado — {task.proceso.trabajador.nombre}',
            descripcion=f'El bloqueo de accesos ha sido confirmado por TI. '
                        f'Proceso de despido #{task.proceso.pk}.',
            proceso=task.proceso,
            tarea=task,
        )
        
        messages.success(request, f'Bloqueo de {task.proceso.trabajador.nombre} confirmado exitosamente.')
        return redirect('ti:bloqueo_urgente')
