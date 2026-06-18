from datetime import timedelta

from django.contrib import messages
from django.db import models as db_models
from django.db.models import Count
from django.shortcuts import redirect, get_object_or_404
from django.utils import timezone
from django.views.generic import TemplateView, ListView

from apps.accounts.decorators import RoleRequiredMixin
from apps.audit.models import AuditLog
from apps.clients.models import CostCenter
from apps.inventory.models import AssetAssignment
from apps.processes.models import Process, Task, TaskDeadlineConfig
from apps.workers.models import Worker

DIAS_REPORTE_ATRAS = 180


AREA_ORDER = ["ti", "prevencion", "logistica", "finanzas"]
AREA_LABELS = {
    "ti": "TI",
    "prevencion": "Prevención",
    "logistica": "Logística",
    "finanzas": "Finanzas",
}


class RRHHDashboardView(RoleRequiredMixin, TemplateView):
    template_name = "rrhh/dashboard.html"
    roles_requeridos = ["administrador", "rrhh"]

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        now = timezone.now()

        workers_activos = Worker.objects.filter(
            estado=Worker.EstadoChoices.ACTIVO
        ).count()

        procesos_activos = Process.objects.filter(
            estado=Process.EstadoChoices.EN_CURSO
        ).count()

        tareas_vencidas = Task.objects.filter(
            omitida=False,
            estado=Task.EstadoChoices.VENCIDA,
            proceso__estado=Process.EstadoChoices.EN_CURSO,
        ).count()

        now + timedelta(days=30)
        contratos_por_vencer = Worker.objects.filter(
            estado=Worker.EstadoChoices.ACTIVO,
            fecha_termino_contrato__isnull=False,
            fecha_termino_contrato__gte=now.date(),
            fecha_termino_contrato__lte=(now + timedelta(days=30)).date(),
        ).count()

        ctx["stats"] = {
            "workers_activos": workers_activos,
            "procesos_activos": procesos_activos,
            "tareas_vencidas": tareas_vencidas,
            "contratos_por_vencer": contratos_por_vencer,
        }

        qs = Task.objects.filter(
            omitida=False,
            proceso__estado=Process.EstadoChoices.EN_CURSO,
        ).select_related("proceso__trabajador", "usuario_responsable")

        ctx["pendientes"] = qs.filter(estado=Task.EstadoChoices.PENDIENTE)
        ctx["en_proceso"] = qs.filter(estado=Task.EstadoChoices.EN_PROCESO)
        ctx["completadas"] = qs.filter(
            estado__in=[
                Task.EstadoChoices.COMPLETADA,
                Task.EstadoChoices.GESTIONADO_EXTERNO,
            ]
        )

        ctx["cargas_area"] = self._get_carga_por_area()

        return ctx

    def _get_carga_por_area(self):
        activas = Task.objects.filter(
            omitida=False,
            proceso__estado=Process.EstadoChoices.EN_CURSO,
            estado__in=[Task.EstadoChoices.PENDIENTE, Task.EstadoChoices.EN_PROCESO],
        )
        resultado = {}
        for area in AREA_ORDER:
            count = activas.filter(
                tipo__in=[k for k, v in Task.TIPO_AREA_MAP.items() if v == area]
            ).count()
            resultado[area] = {
                "label": AREA_LABELS.get(area, area),
                "count": count,
            }
        return resultado


class RRHHTrabajadoresView(RoleRequiredMixin, ListView):
    model = Worker
    template_name = "rrhh/trabajadores.html"
    context_object_name = "workers"
    roles_requeridos = ["administrador", "rrhh"]
    paginate_by = 20

    def get_queryset(self):
        qs = Worker.objects.select_related("centro_costo_actual")

        q = self.request.GET.get("q", "").strip()
        estado = self.request.GET.get("estado", "")
        ceco = self.request.GET.get("ceco", "")
        cargo = self.request.GET.get("cargo", "")

        if q:
            qs = qs.filter(
                db_models.Q(nombre__icontains=q) | db_models.Q(run__icontains=q)
            )
        if estado:
            qs = qs.filter(estado=estado)
        if ceco:
            qs = qs.filter(centro_costo_actual_id=ceco)
        if cargo:
            qs = qs.filter(cargo__icontains=cargo)

        if not self.request.GET.get("incluir_eliminados"):
            qs = qs.exclude(estado=Worker.EstadoChoices.ELIMINADO)

        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["query"] = self.request.GET.get("q", "")
        ctx["filtro_estado"] = self.request.GET.get("estado", "")
        ctx["filtro_ceco"] = self.request.GET.get("ceco", "")
        ctx["filtro_cargo"] = self.request.GET.get("cargo", "")
        ctx["incluir_eliminados"] = self.request.GET.get("incluir_eliminados", "")
        ctx["costcenters"] = CostCenter.objects.filter(estado="activo")
        return ctx


class RRHHProcesosView(RoleRequiredMixin, ListView):
    model = Process
    template_name = "rrhh/procesos.html"
    context_object_name = "processes"
    roles_requeridos = ["administrador", "rrhh"]
    paginate_by = 20

    def get_queryset(self):
        qs = Process.objects.select_related(
            "trabajador", "usuario_inicio", "ceco_origen", "ceco_destino"
        )

        tipo = self.request.GET.get("tipo", "")
        estado = self.request.GET.get("estado", "")
        if tipo:
            qs = qs.filter(tipo=tipo)
        if estado:
            qs = qs.filter(estado=estado)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["filtro_tipo"] = self.request.GET.get("tipo", "")
        ctx["filtro_estado"] = self.request.GET.get("estado", "")
        return ctx


class RRHHCecosView(RoleRequiredMixin, ListView):
    model = CostCenter
    template_name = "rrhh/cecos.html"
    context_object_name = "costcenters"
    roles_requeridos = ["administrador", "rrhh"]
    paginate_by = 20

    def get_queryset(self):
        qs = CostCenter.objects.select_related("cliente", "jefatura")

        q = self.request.GET.get("q", "").strip()
        estado = self.request.GET.get("estado", "")
        if q:
            qs = qs.filter(
                db_models.Q(nombre__icontains=q)
                | db_models.Q(codigo__icontains=q)
                | db_models.Q(cliente__nombre__icontains=q)
            )
        if estado:
            qs = qs.filter(estado=estado)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["query"] = self.request.GET.get("q", "")
        ctx["filtro_estado"] = self.request.GET.get("estado", "")
        return ctx


class RRHHReportesView(RoleRequiredMixin, TemplateView):
    template_name = "rrhh/reportes.html"
    roles_requeridos = ["administrador", "rrhh"]

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        total_workers = Worker.objects.exclude(
            estado=Worker.EstadoChoices.ELIMINADO
        ).count()
        workers_activos = Worker.objects.filter(
            estado=Worker.EstadoChoices.ACTIVO
        ).count()
        workers_en_proceso = Worker.objects.filter(
            estado=Worker.EstadoChoices.EN_PROCESO
        ).count()
        workers_desvinculados = Worker.objects.filter(
            estado=Worker.EstadoChoices.DESVINCULADO
        ).count()

        ctx["resumen_workers"] = {
            "total": total_workers,
            "activos": workers_activos,
            "en_proceso": workers_en_proceso,
            "desvinculados": workers_desvinculados,
        }

        distribucion_ceco = (
            Worker.objects.filter(
                estado=Worker.EstadoChoices.ACTIVO,
                centro_costo_actual__isnull=False,
            )
            .values("centro_costo_actual__nombre")
            .annotate(cantidad=Count("id"))
            .order_by("-cantidad")[:10]
        )

        ctx["distribucion_ceco"] = list(distribucion_ceco)

        now = timezone.now()
        ultimos_6_meses = now - timedelta(days=DIAS_REPORTE_ATRAS)

        ingresos_recientes = Worker.objects.filter(
            fecha_ingreso_efectiva__gte=ultimos_6_meses,
            fecha_ingreso_efectiva__isnull=False,
        ).count()

        ctx["ingresos_recientes"] = ingresos_recientes

        procesos_por_tipo = (
            Process.objects.filter(
                estado=Process.EstadoChoices.EN_CURSO,
            )
            .values("tipo")
            .annotate(cantidad=Count("id"))
            .order_by("-cantidad")
        )

        ctx["procesos_por_tipo"] = list(procesos_por_tipo)

        total_procesos = Process.objects.count()
        procesos_completados = Process.objects.filter(
            estado=Process.EstadoChoices.COMPLETADO
        ).count()
        procesos_en_curso = Process.objects.filter(
            estado=Process.EstadoChoices.EN_CURSO
        ).count()

        ctx["resumen_procesos"] = {
            "total": total_procesos,
            "completados": procesos_completados,
            "en_curso": procesos_en_curso,
        }

        return ctx


class RRHHConfigPlazosView(RoleRequiredMixin, TemplateView):
    template_name = "rrhh/config_plazos.html"
    roles_requeridos = ["administrador", "rrhh"]

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["configs"] = TaskDeadlineConfig.objects.all().order_by("tipo_tarea")
        return ctx

    def post(self, request, *args, **kwargs):
        config_id = request.POST.get("config_id")
        config = get_object_or_404(TaskDeadlineConfig, pk=config_id)

        config.plazo_dias = int(request.POST.get("plazo_dias", config.plazo_dias))
        config.plazo_escalamiento_dias = int(
            request.POST.get("plazo_escalamiento_dias", config.plazo_escalamiento_dias)
        )
        config.es_critica = request.POST.get("es_critica") == "on"

        try:
            config.full_clean()
            config.save()
            messages.success(
                request, f"Plazo actualizado para {config.get_tipo_tarea_display()}."
            )
        except Exception as e:
            messages.error(request, f"Error: {e}")

        return redirect("rrhh:config_plazos")


class RRHHAlertasContratosView(RoleRequiredMixin, ListView):
    model = Worker
    template_name = "rrhh/alertas_contratos.html"
    context_object_name = "workers"
    roles_requeridos = ["administrador", "rrhh"]
    paginate_by = 20

    def get_queryset(self):
        now = timezone.now().date()
        filtro = self.request.GET.get("filtro", "30")

        try:
            dias = int(filtro)
        except ValueError:
            dias = 30

        hasta = now + timedelta(days=dias)

        qs = (
            Worker.objects.filter(
                estado=Worker.EstadoChoices.ACTIVO,
                fecha_termino_contrato__isnull=False,
                fecha_termino_contrato__lte=hasta,
                fecha_termino_contrato__gte=now,
            )
            .select_related("centro_costo_actual")
            .order_by("fecha_termino_contrato")
        )

        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        now = timezone.now().date()
        ctx["filtro"] = self.request.GET.get("filtro", "30")
        ctx["total_alertas"] = Worker.objects.filter(
            estado=Worker.EstadoChoices.ACTIVO,
            fecha_termino_contrato__isnull=False,
            fecha_termino_contrato__gte=now,
        ).count()
        return ctx


class RRHHConfirmarCierreTerminoView(RoleRequiredMixin, TemplateView):
    template_name = "rrhh/confirmar_cierre_termino.html"
    roles_requeridos = ["administrador", "rrhh"]

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        proceso_id = self.kwargs.get("pk")
        proceso = get_object_or_404(
            Process, pk=proceso_id, tipo=Process.TipoChoices.TERMINO
        )

        tareas = proceso.tareas.all()
        todas_completas = (
            tareas.filter(
                estado__in=[
                    Task.EstadoChoices.COMPLETADA,
                    Task.EstadoChoices.GESTIONADO_EXTERNO,
                ]
            ).count()
            == tareas.count()
        )

        ctx["proceso"] = proceso
        ctx["tareas"] = tareas
        ctx["todas_completas"] = todas_completas

        return ctx

    def post(self, request, *args, **kwargs):
        proceso_id = request.POST.get("proceso_id")
        proceso = get_object_or_404(
            Process, pk=proceso_id, tipo=Process.TipoChoices.TERMINO
        )

        from apps.processes.services import _finalizar_proceso

        _finalizar_proceso(proceso)

        messages.success(
            request, f"Término de contrato de {proceso.trabajador.nombre} confirmado."
        )
        return redirect("rrhh:procesos")


class RRHHProcesoDetailView(RoleRequiredMixin, TemplateView):
    """
    RF-08/RF-17/RF-26/RF-35: Vista de detalle de proceso con historial completo.
    Muestra información del proceso, tareas, activos asignados y bitácora de auditoría.
    """

    template_name = "rrhh/proceso_detalle.html"
    roles_requeridos = ["administrador", "rrhh"]

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        proceso_id = self.kwargs.get("pk")
        proceso = get_object_or_404(
            Process.objects.select_related(
                "trabajador", "usuario_inicio", "ceco_origen", "ceco_destino"
            ),
            pk=proceso_id,
        )

        # Tareas del proceso
        tareas = proceso.tareas.all().select_related("usuario_responsable")

        # Activos asignados en este proceso
        activos_asignados = AssetAssignment.objects.filter(
            proceso=proceso
        ).select_related("activo__tipo", "trabajador")

        # Historial de auditoría del proceso
        historial = AuditLog.objects.filter(
            tabla_afectada="proceso",
            id_entidad_afectada=proceso.pk,
        ).select_related("usuario")[:50]

        # Historial de CeCo si es cambio de CeCo
        historial_ceco = None
        if proceso.tipo == Process.TipoChoices.CAMBIO_CECO:
            historial_ceco = proceso.trabajador.historial_ceco.select_related(
                "centro_costo"
            ).all()

        ctx["proceso"] = proceso
        ctx["tareas"] = tareas
        ctx["activos_asignados"] = activos_asignados
        ctx["historial"] = historial
        ctx["historial_ceco"] = historial_ceco

        return ctx
