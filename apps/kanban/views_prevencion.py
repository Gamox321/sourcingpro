from datetime import timedelta

from django.db import models as db_models
from django.utils import timezone
from django.views.generic import TemplateView, ListView

from apps.accounts.decorators import RoleRequiredMixin
from apps.inventory.models import Asset, AssetType
from apps.processes.models import Process, Task


PREVENCION_TASK_TYPES = [
    Task.TipoChoices.EXAMENES_PREOCUPACIONALES,
    Task.TipoChoices.EPP_INDUCCION,
]


class PrevencionDashboardView(RoleRequiredMixin, TemplateView):
    template_name = 'prevencion/dashboard.html'
    roles_requeridos = ['prevencion']

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        
        now = timezone.now()
        
        mis_tareas = Task.objects.filter(
            usuario_responsable=self.request.user,
            tipo__in=PREVENCION_TASK_TYPES,
            omitida=False,
            proceso__estado=Process.EstadoChoices.EN_CURSO,
        ).select_related('proceso__trabajador', 'proceso__ceco_origen', 'proceso__ceco_destino')
        
        tareas_activas = mis_tareas.filter(
            estado__in=[Task.EstadoChoices.PENDIENTE, Task.EstadoChoices.EN_PROCESO]
        )
        
        try:
            tipo_epp = AssetType.objects.get(nombre__icontains='EPP')
            epp_total = Asset.objects.filter(tipo=tipo_epp)
            epp_asignados = epp_total.filter(estado=Asset.EstadoChoices.ASIGNADO).count()
            epp_disponibles = epp_total.filter(estado=Asset.EstadoChoices.DISPONIBLE).count()
        except AssetType.DoesNotExist:
            epp_asignados = 0
            epp_disponibles = 0
        
        examenes_pendientes = mis_tareas.filter(
            tipo=Task.TipoChoices.EXAMENES_PREOCUPACIONALES,
            estado__in=[Task.EstadoChoices.PENDIENTE, Task.EstadoChoices.EN_PROCESO],
            plazo_limite__lte=now + timedelta(days=7),
        ).count()
        
        ctx['stats'] = {
            'tareas_activas': tareas_activas.count(),
            'epp_asignados': epp_asignados,
            'epp_disponibles': epp_disponibles,
            'examenes_pendientes': examenes_pendientes,
        }
        
        ctx['mis_tareas'] = tareas_activas.order_by('-urgencia', 'plazo_limite')[:10]
        
        try:
            tipo_epp = AssetType.objects.get(nombre__icontains='EPP')
            inventario_epp = Asset.objects.filter(
                tipo=tipo_epp
            ).select_related('tipo').prefetch_related('asignaciones__trabajador')[:10]
        except AssetType.DoesNotExist:
            inventario_epp = Asset.objects.none()
        
        ctx['inventario_epp'] = inventario_epp
        
        return ctx


class PrevencionInventarioView(RoleRequiredMixin, ListView):
    model = Asset
    template_name = 'prevencion/inventario.html'
    context_object_name = 'assets'
    roles_requeridos = ['prevencion']
    paginate_by = 20

    def get_queryset(self):
        try:
            tipo_epp = AssetType.objects.get(nombre__icontains='EPP')
            qs = Asset.objects.filter(tipo=tipo_epp).select_related('tipo')
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


class PrevencionCertificacionesView(RoleRequiredMixin, TemplateView):
    template_name = 'prevencion/certificaciones.html'
    roles_requeridos = ['prevencion']

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        
        now = timezone.now()
        prox_30_dias = now + timedelta(days=30)
        
        tareas_certificaciones = Task.objects.filter(
            tipo=Task.TipoChoices.EXAMENES_PREOCUPACIONALES,
            omitida=False,
            proceso__estado=Process.EstadoChoices.EN_CURSO,
            estado__in=[Task.EstadoChoices.PENDIENTE, Task.EstadoChoices.EN_PROCESO],
            plazo_limite__lte=prox_30_dias,
        ).select_related('proceso__trabajador').order_by('plazo_limite')
        
        certificaciones = []
        for tarea in tareas_certificaciones:
            dias_restantes = (tarea.plazo_limite - now).days if tarea.plazo_limite else 0
            
            if dias_restantes <= 7:
                urgencia = 'critica'
            elif dias_restantes <= 14:
                urgencia = 'alta'
            else:
                urgencia = 'normal'
            
            certificaciones.append({
                'tarea': tarea,
                'dias_restantes': dias_restantes,
                'urgencia': urgencia,
            })
        
        ctx['certificaciones'] = certificaciones
        ctx['total_certificaciones'] = len(certificaciones)
        
        return ctx


class PrevencionTableroGeneralView(RoleRequiredMixin, TemplateView):
    template_name = 'prevencion/tablero.html'
    roles_requeridos = ['prevencion']

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        
        qs = Task.objects.filter(
            tipo__in=PREVENCION_TASK_TYPES,
            omitida=False,
            proceso__estado=Process.EstadoChoices.EN_CURSO,
        ).select_related('proceso__trabajador', 'usuario_responsable')
        
        ctx['pendientes'] = qs.filter(estado=Task.EstadoChoices.PENDIENTE)
        ctx['en_proceso'] = qs.filter(estado=Task.EstadoChoices.EN_PROCESO)
        ctx['completadas'] = qs.filter(
            estado__in=[Task.EstadoChoices.COMPLETADA, Task.EstadoChoices.GESTIONADO_EXTERNO]
        )
        
        return ctx


class PrevencionNotificacionesView(RoleRequiredMixin, ListView):
    template_name = 'prevencion/notificaciones.html'
    context_object_name = 'notifications'
    roles_requeridos = ['prevencion']
    paginate_by = 30

    def get_queryset(self):
        from apps.notifications.models import Notification
        qs = Notification.objects.filter(
            usuario_destinatario=self.request.user,
        ).exclude(estado=Notification.EstadoChoices.ELIMINADA)

        filtro = self.request.GET.get('filtro', '')
        if filtro == 'no_leidas':
            qs = qs.filter(estado=Notification.EstadoChoices.ENVIADA)
        elif filtro == 'leidas':
            qs = qs.filter(estado=Notification.EstadoChoices.LEIDA)

        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        from apps.notifications.models import Notification
        ctx['filtro'] = self.request.GET.get('filtro', '')
        ctx['no_leidas'] = Notification.objects.filter(
            usuario_destinatario=self.request.user,
            estado=Notification.EstadoChoices.ENVIADA,
        ).count()
        return ctx
