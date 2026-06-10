from django.utils import timezone
from django.views.generic import TemplateView, ListView

from apps.accounts.decorators import RoleRequiredMixin
from apps.notifications.models import Notification
from apps.notifications.views import NotificationListView
from apps.processes.models import Process, Task


class FinanzasNotificacionesView(NotificationListView):
    template_name = 'finanzas/notificaciones.html'
    roles_requeridos = ['administrador', 'finanzas']


class FinanzasDashboardView(RoleRequiredMixin, TemplateView):
    template_name = 'finanzas/dashboard.html'
    roles_requeridos = ['administrador', 'finanzas']

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        now = timezone.now()
        primer_dia_mes = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        # Tareas de Finanzas
        mis_tareas = Task.objects.filter(
            tipo=Task.TipoChoices.FINIQUITO_COORDINACION,
            omitida=False,
            proceso__estado=Process.EstadoChoices.EN_CURSO,
        ).select_related('proceso__trabajador', 'usuario_responsable')

        tareas_pendientes = mis_tareas.filter(
            estado__in=[Task.EstadoChoices.PENDIENTE, Task.EstadoChoices.EN_PROCESO]
        )

        # Finiquitos coordinados este mes
        finiquitos_mes = Task.objects.filter(
            tipo=Task.TipoChoices.FINIQUITO_COORDINACION,
            estado__in=[Task.EstadoChoices.COMPLETADA, Task.EstadoChoices.GESTIONADO_EXTERNO],
            fecha_completado__gte=primer_dia_mes,
        ).count()

        # Procesos de término activos
        termino_activos = Process.objects.filter(
            tipo=Process.TipoChoices.TERMINO,
            estado=Process.EstadoChoices.EN_CURSO,
        ).count()

        # Procesos de despido activos
        despido_activos = Process.objects.filter(
            tipo=Process.TipoChoices.DESPIDO,
            estado=Process.EstadoChoices.EN_CURSO,
        ).count()

        # Tareas vencidas de Finanzas
        tareas_vencidas = mis_tareas.filter(
            estado=Task.EstadoChoices.VENCIDA,
        ).count()

        ctx['stats'] = {
            'tareas_pendientes': tareas_pendientes.count(),
            'finiquitos_mes': finiquitos_mes,
            'termino_activos': termino_activos,
            'despido_activos': despido_activos,
            'tareas_vencidas': tareas_vencidas,
        }

        ctx['mis_tareas'] = tareas_pendientes.order_by('-urgencia', 'plazo_limite')[:10]

        return ctx


class FinanzasFiniquitosView(RoleRequiredMixin, ListView):
    model = Process
    template_name = 'finanzas/finiquitos.html'
    context_object_name = 'procesos'
    roles_requeridos = ['administrador', 'finanzas']
    paginate_by = 20

    def get_queryset(self):
        qs = Process.objects.filter(
            tipo__in=[Process.TipoChoices.TERMINO, Process.TipoChoices.DESPIDO],
            estado=Process.EstadoChoices.EN_CURSO,
        ).select_related('trabajador', 'usuario_inicio', 'ceco_origen')

        tipo = self.request.GET.get('tipo', '')
        if tipo:
            qs = qs.filter(tipo=tipo)

        return qs.order_by('-fecha_inicio')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['filtro_tipo'] = self.request.GET.get('tipo', '')
        return ctx


class FinanzasTableroView(RoleRequiredMixin, TemplateView):
    template_name = 'finanzas/tablero.html'
    roles_requeridos = ['administrador', 'finanzas']

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        qs = Task.objects.filter(
            tipo=Task.TipoChoices.FINIQUITO_COORDINACION,
            omitida=False,
            proceso__estado=Process.EstadoChoices.EN_CURSO,
        ).select_related('proceso__trabajador', 'usuario_responsable')

        ctx['pendientes'] = qs.filter(estado=Task.EstadoChoices.PENDIENTE)
        ctx['en_proceso'] = qs.filter(estado=Task.EstadoChoices.EN_PROCESO)
        ctx['completadas'] = qs.filter(
            estado__in=[Task.EstadoChoices.COMPLETADA, Task.EstadoChoices.GESTIONADO_EXTERNO]
        )

        return ctx
