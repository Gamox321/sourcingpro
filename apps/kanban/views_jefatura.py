from datetime import date

from django.shortcuts import get_object_or_404
from django.views.generic import TemplateView, ListView, DetailView

from apps.accounts.decorators import RoleRequiredMixin
from apps.clients.models import CostCenter
from apps.inventory.models import AssetAssignment
from apps.notifications.views import NotificationListView
from apps.processes.models import Process, Task
from apps.workers.models import Worker


class JefaturaNominaView(RoleRequiredMixin, TemplateView):
    template_name = 'jefatura/nomina.html'
    roles_requeridos = ['administrador', 'jefatura']

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user
        
        cecos = user.cecos_a_cargo.filter(estado=CostCenter.EstadoChoices.ACTIVO)
        ceco_id = self.request.GET.get('ceco')
        
        if ceco_id:
            ceco_seleccionado = get_object_or_404(cecos, pk=ceco_id)
        else:
            ceco_seleccionado = cecos.first()
        
        for ceco in cecos:
            ceco.workers_activos = Worker.objects.filter(
                centro_costo_actual=ceco
            ).exclude(estado=Worker.EstadoChoices.ELIMINADO).count()
        
        ctx['cecos'] = cecos
        ctx['ceco_seleccionado'] = ceco_seleccionado
        
        if ceco_seleccionado:
            workers = Worker.objects.filter(
                centro_costo_actual=ceco_seleccionado
            ).exclude(estado=Worker.EstadoChoices.ELIMINADO).order_by('nombre')
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
    roles_requeridos = ['administrador', 'jefatura']

    def get_template_names(self):
        if self.request.headers.get('HX-Request') == 'true':
            return ['jefatura/_trabajador_ficha.html']
        return ['jefatura/trabajador_detail.html']

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user
        worker_id = self.kwargs.get('pk')
        
        cecos = user.cecos_a_cargo.filter(estado=CostCenter.EstadoChoices.ACTIVO)
        worker = get_object_or_404(
            Worker.objects.select_related('centro_costo_actual'),
            pk=worker_id,
            centro_costo_actual__in=cecos
        )
        
        if worker.fecha_termino_contrato:
            worker.dias_restantes_contrato = (worker.fecha_termino_contrato - date.today()).days
        
        ctx['worker'] = worker
        
        procesos_activos = Process.objects.filter(
            trabajador=worker,
            estado=Process.EstadoChoices.EN_CURSO
        ).select_related('ceco_origen', 'ceco_destino').prefetch_related('tareas')
        
        for p in procesos_activos:
            p.tareas_completadas = sum(
                1 for t in p.tareas.all()
                if t.estado in (Task.EstadoChoices.COMPLETADA, Task.EstadoChoices.GESTIONADO_EXTERNO)
            )
        
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
    roles_requeridos = ['administrador', 'jefatura']

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user
        
        cecos = user.cecos_a_cargo.filter(estado=CostCenter.EstadoChoices.ACTIVO)
        ceco_id = self.request.GET.get('ceco')
        
        if ceco_id:
            ceco_seleccionado = get_object_or_404(cecos, pk=ceco_id)
        else:
            ceco_seleccionado = cecos.first()
        
        ctx['cecos'] = cecos
        ctx['ceco_seleccionado'] = ceco_seleccionado
        
        tipo_proceso = self.request.GET.get('tipo_proceso', '')
        ctx['filtro_tipo_proceso'] = tipo_proceso
        
        if ceco_seleccionado:
            workers_ceco = Worker.objects.filter(centro_costo_actual=ceco_seleccionado)
            
            tareas = Task.objects.filter(
                proceso__trabajador__in=workers_ceco,
                omitida=False,
                proceso__estado=Process.EstadoChoices.EN_CURSO
            ).select_related('proceso__trabajador', 'usuario_responsable', 'proceso__ceco_origen', 'proceso__ceco_destino')
            
            if tipo_proceso:
                tareas = tareas.filter(proceso__tipo=tipo_proceso)
        else:
            tareas = Task.objects.none()
        
        ctx['tareas_pendientes'] = tareas.filter(estado=Task.EstadoChoices.PENDIENTE)
        ctx['tareas_en_proceso'] = tareas.filter(estado=Task.EstadoChoices.EN_PROCESO)
        ctx['tareas_completadas'] = tareas.filter(estado=Task.EstadoChoices.COMPLETADA)
        
        return ctx


class JefaturaProcesosView(RoleRequiredMixin, ListView):
    template_name = 'jefatura/procesos.html'
    context_object_name = 'procesos'
    roles_requeridos = ['administrador', 'jefatura']
    paginate_by = 20

    def get_queryset(self):
        user = self.request.user
        cecos = user.cecos_a_cargo.filter(estado=CostCenter.EstadoChoices.ACTIVO)
        ceco_id = self.request.GET.get('ceco')
        
        if ceco_id:
            self.ceco_seleccionado = get_object_or_404(cecos, pk=ceco_id)
        else:
            self.ceco_seleccionado = cecos.first()
        
        if not self.ceco_seleccionado:
            return Process.objects.none()
        
        workers_ceco = Worker.objects.filter(centro_costo_actual=self.ceco_seleccionado)
        procesos = Process.objects.filter(
            trabajador__in=workers_ceco,
            estado=Process.EstadoChoices.EN_CURSO
        ).select_related('trabajador', 'usuario_inicio', 'ceco_origen', 'ceco_destino')
        
        tipo = self.request.GET.get('tipo')
        if tipo:
            procesos = procesos.filter(tipo=tipo)
        
        return procesos.order_by('-fecha_inicio')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user
        cecos = user.cecos_a_cargo.filter(estado=CostCenter.EstadoChoices.ACTIVO)
        ceco_id = self.request.GET.get('ceco')
        
        if not ceco_id:
            ceco_seleccionado = cecos.first()
        elif hasattr(self, 'ceco_seleccionado'):
            ceco_seleccionado = self.ceco_seleccionado
        else:
            ceco_seleccionado = cecos.first()
        
        ctx['cecos'] = cecos
        ctx['ceco_seleccionado'] = ceco_seleccionado
        ctx['filtro_tipo'] = self.request.GET.get('tipo', '')
        return ctx


class JefaturaCeCoView(RoleRequiredMixin, DetailView):
    template_name = 'jefatura/ceco.html'
    context_object_name = 'ceco'
    roles_requeridos = ['administrador', 'jefatura']

    def get_object(self):
        user = self.request.user
        cecos = user.cecos_a_cargo.filter(estado=CostCenter.EstadoChoices.ACTIVO)
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
            ).exclude(estado=Worker.EstadoChoices.ELIMINADO)
            
            ctx['total_workers'] = workers.count()
            ctx['workers_activos'] = workers.filter(estado=Worker.EstadoChoices.ACTIVO).count()
            ctx['workers_en_transito'] = workers.filter(estado=Worker.EstadoChoices.EN_TRANSITO).count()
            ctx['workers_por_egresar'] = workers.filter(estado=Worker.EstadoChoices.POR_EGRESAR).count()
            
            ctx['procesos_activos'] = Process.objects.filter(
                trabajador__in=workers,
                estado=Process.EstadoChoices.EN_CURSO
            ).count()
        
        user = self.request.user
        ctx['cecos'] = user.cecos_a_cargo.filter(estado=CostCenter.EstadoChoices.ACTIVO)
        
        return ctx


class JefaturaNotificacionesView(NotificationListView):
    template_name = 'jefatura/notificaciones.html'
    roles_requeridos = ['administrador', 'jefatura']
