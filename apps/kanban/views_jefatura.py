from django.shortcuts import get_object_or_404
from django.views.generic import TemplateView, ListView, DetailView

from apps.accounts.decorators import RoleRequiredMixin
from apps.clients.models import CostCenter
from apps.inventory.models import AssetAssignment
from apps.processes.models import Process, Task
from apps.workers.models import Worker


class JefaturaNominaView(RoleRequiredMixin, TemplateView):
    template_name = 'jefatura/nomina.html'
    roles_requeridos = ['jefatura']

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user
        
        cecos = user.cecos_a_cargo.filter(estado='activo')
        ceco_id = self.request.GET.get('ceco')
        
        if ceco_id:
            ceco_seleccionado = get_object_or_404(cecos, pk=ceco_id)
        else:
            ceco_seleccionado = cecos.first()
        
        ctx['cecos'] = cecos
        ctx['ceco_seleccionado'] = ceco_seleccionado
        
        if ceco_seleccionado:
            workers = Worker.objects.filter(
                centro_costo_actual=ceco_seleccionado
            ).exclude(estado='eliminado').order_by('nombre')
        else:
            workers = Worker.objects.none()
        
        estado_filter = self.request.GET.get('estado')
        if estado_filter:
            workers = workers.filter(estado=estado_filter)
        
        q = self.request.GET.get('q', '').strip()
        if q:
            workers = workers.filter(nombre__icontains=q)
        
        ctx['workers'] = workers
        ctx['total_workers'] = workers.count()
        ctx['filtro_estado'] = estado_filter
        ctx['query'] = q
        
        return ctx


class JefaturaTrabajadorDetailView(RoleRequiredMixin, TemplateView):
    template_name = 'jefatura/_trabajador_ficha.html'
    roles_requeridos = ['jefatura']

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user
        worker_id = self.kwargs.get('pk')
        
        cecos = user.cecos_a_cargo.filter(estado='activo')
        worker = get_object_or_404(
            Worker.objects.select_related('centro_costo_actual'),
            pk=worker_id,
            centro_costo_actual__in=cecos
        )
        
        ctx['worker'] = worker
        
        procesos_activos = Process.objects.filter(
            trabajador=worker,
            estado='en_curso'
        ).select_related('ceco_origen', 'ceco_destino')
        ctx['procesos_activos'] = procesos_activos
        
        activos = AssetAssignment.objects.filter(
            trabajador=worker,
            fecha_devolucion__isnull=True
        ).select_related('activo__tipo')
        ctx['activos'] = activos
        
        historial = Process.objects.filter(
            trabajador=worker
        ).select_related('usuario_inicio').order_by('-fecha_inicio')[:10]
        ctx['historial'] = historial
        
        return ctx


class JefaturaTableroView(RoleRequiredMixin, TemplateView):
    template_name = 'jefatura/tablero.html'
    roles_requeridos = ['jefatura']

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user
        
        cecos = user.cecos_a_cargo.filter(estado='activo')
        ceco_id = self.request.GET.get('ceco')
        
        if ceco_id:
            ceco_seleccionado = get_object_or_404(cecos, pk=ceco_id)
        else:
            ceco_seleccionado = cecos.first()
        
        ctx['cecos'] = cecos
        ctx['ceco_seleccionado'] = ceco_seleccionado
        
        if ceco_seleccionado:
            workers_ceco = Worker.objects.filter(centro_costo_actual=ceco_seleccionado)
            
            tareas = Task.objects.filter(
                proceso__trabajador__in=workers_ceco,
                omitida=False,
                proceso__estado='en_curso'
            ).select_related('proceso__trabajador', 'usuario_responsable')
        else:
            tareas = Task.objects.none()
        
        ctx['tareas_pendientes'] = tareas.filter(estado='pendiente')
        ctx['tareas_en_proceso'] = tareas.filter(estado='en_proceso')
        ctx['tareas_completadas'] = tareas.filter(estado='completada')
        
        return ctx


class JefaturaProcesosView(RoleRequiredMixin, ListView):
    template_name = 'jefatura/procesos.html'
    context_object_name = 'procesos'
    roles_requeridos = ['jefatura']
    paginate_by = 20

    def get_queryset(self):
        user = self.request.user
        cecos = user.cecos_a_cargo.filter(estado='activo')
        ceco_id = self.request.GET.get('ceco')
        
        if ceco_id:
            ceco_seleccionado = get_object_or_404(cecos, pk=ceco_id)
        else:
            ceco_seleccionado = cecos.first()
        
        self.ceco_seleccionado = ceco_seleccionado
        self.cecos = cecos
        
        if ceco_seleccionado:
            workers_ceco = Worker.objects.filter(centro_costo_actual=ceco_seleccionado)
            procesos = Process.objects.filter(
                trabajador__in=workers_ceco,
                estado='en_curso'
            ).select_related('trabajador', 'usuario_inicio', 'ceco_origen', 'ceco_destino')
        else:
            procesos = Process.objects.none()
        
        tipo_filter = self.request.GET.get('tipo')
        if tipo_filter:
            procesos = procesos.filter(tipo=tipo_filter)
        
        self.filtro_tipo = tipo_filter
        
        return procesos.order_by('-fecha_inicio')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['cecos'] = self.cecos
        ctx['ceco_seleccionado'] = self.ceco_seleccionado
        ctx['filtro_tipo'] = getattr(self, 'filtro_tipo', None)
        return ctx


class JefaturaCeCoView(RoleRequiredMixin, DetailView):
    template_name = 'jefatura/ceco.html'
    context_object_name = 'ceco'
    roles_requeridos = ['jefatura']

    def get_object(self):
        user = self.request.user
        cecos = user.cecos_a_cargo.filter(estado='activo')
        ceco_id = self.kwargs.get('pk') or self.request.GET.get('ceco')
        
        if ceco_id:
            return get_object_or_404(cecos, pk=ceco_id)
        return cecos.first()

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ceco = self.object
        
        if ceco:
            workers = Worker.objects.filter(
                centro_costo_actual=ceco
            ).exclude(estado='eliminado')
            
            ctx['total_workers'] = workers.count()
            ctx['workers_activos'] = workers.filter(estado='activo').count()
            ctx['workers_en_transito'] = workers.filter(estado='en_transito').count()
            ctx['workers_por_egresar'] = workers.filter(estado='por_egresar').count()
            
            ctx['procesos_activos'] = Process.objects.filter(
                trabajador__in=workers,
                estado='en_curso'
            ).count()
        
        user = self.request.user
        ctx['cecos'] = user.cecos_a_cargo.filter(estado='activo')
        
        return ctx


class JefaturaNotificacionesView(RoleRequiredMixin, ListView):
    template_name = 'jefatura/notificaciones.html'
    context_object_name = 'notifications'
    roles_requeridos = ['jefatura']
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
