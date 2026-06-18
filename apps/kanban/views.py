from datetime import timedelta

from django.db import models as db_models
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.views.generic import TemplateView, View

from apps.accounts.decorators import RoleRequiredMixin
from apps.processes.models import Task, Process


AREA_ORDER = ["ti", "prevencion", "logistica", "finanzas"]
AREA_LABELS = {
    "ti": "TI",
    "prevencion": "Prevención",
    "logistica": "Logística",
    "finanzas": "Finanzas",
}


def _get_tasks_queryset(request):
    qs = Task.objects.filter(
        omitida=False,
        proceso__estado=Process.EstadoChoices.EN_CURSO,
    ).select_related(
        "proceso__trabajador",
        "usuario_responsable",
    )

    q = request.GET.get("q", "").strip()
    tipo_proceso = request.GET.get("tipo_proceso", "")
    area = request.GET.get("area", "")
    trabajador = request.GET.get("trabajador", "")
    mostrar_archivadas = request.GET.get("archivadas", "")

    if not mostrar_archivadas:
        hace_3_dias = timezone.now() - timedelta(days=3)
        qs = qs.filter(
            db_models.Q(proceso__fecha_cierre__isnull=True)
            | db_models.Q(proceso__fecha_cierre__gte=hace_3_dias)
        )

    if q:
        qs = qs.filter(
            db_models.Q(proceso__trabajador__nombre__icontains=q)
            | db_models.Q(proceso__trabajador__run__icontains=q)
        )
    if tipo_proceso:
        qs = qs.filter(proceso__tipo=tipo_proceso)
    if area:
        qs = qs.filter(tipo__in=[k for k, v in Task.TIPO_AREA_MAP.items() if v == area])
    if trabajador:
        qs = qs.filter(proceso__trabajador_id=trabajador)

    return qs


class KanbanBoardView(RoleRequiredMixin, TemplateView):
    template_name = "kanban/board.html"
    roles_requeridos = ["administrador", "ti", "prevencion", "finanzas", "logistica"]

    def get_template_names(self):
        if self.request.headers.get("HX-Request") == "true" or self.request.GET.get("partial"):
            return ["kanban/_board_partial.html"]
        return ["kanban/board.html"]

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        qs = _get_tasks_queryset(self.request)

        ctx["pendientes"] = qs.filter(estado=Task.EstadoChoices.PENDIENTE)
        ctx["en_proceso"] = qs.filter(estado=Task.EstadoChoices.EN_PROCESO)
        ctx["completadas"] = qs.filter(
            estado__in=[
                Task.EstadoChoices.COMPLETADA,
                Task.EstadoChoices.GESTIONADO_EXTERNO,
            ]
        )

        ctx["user_roles"] = set(
            self.request.user.roles.values_list("nombre", flat=True)
        )

        ctx.update(
            {
                "filtro_q": self.request.GET.get("q", ""),
                "filtro_tipo_proceso": self.request.GET.get("tipo_proceso", ""),
                "filtro_area": self.request.GET.get("area", ""),
                "filtro_trabajador": self.request.GET.get("trabajador", ""),
                "mostrar_archivadas": self.request.GET.get("archivadas", ""),
            }
        )

        ctx["cargas_area"] = self._get_carga_por_area()
        ctx["resumen"] = self._get_resumen()

        return ctx

    def _get_resumen(self):
        from apps.workers.models import Worker
        from apps.notifications.models import Notification

        timezone.now()
        activos = Process.objects.filter(estado=Process.EstadoChoices.EN_CURSO).count()
        tareas_pendientes = Task.objects.filter(
            omitida=False,
            estado=Task.EstadoChoices.PENDIENTE,
            proceso__estado=Process.EstadoChoices.EN_CURSO,
        ).count()
        tareas_criticas = Task.objects.filter(
            omitida=False,
            urgencia=Task.UrgenciaChoices.CRITICA,
            estado__in=[Task.EstadoChoices.PENDIENTE, Task.EstadoChoices.EN_PROCESO],
        ).count()
        workers_activos = Worker.objects.filter(
            estado=Worker.EstadoChoices.ACTIVO
        ).count()
        notif_recientes = Notification.objects.filter(
            usuario_destinatario=self.request.user,
            estado=Notification.EstadoChoices.ENVIADA,
            canal="interno",
        ).count()
        vencidas_hoy = Task.objects.filter(
            omitida=False,
            estado=Task.EstadoChoices.VENCIDA,
            proceso__estado=Process.EstadoChoices.EN_CURSO,
        ).count()
        return {
            "procesos_activos": activos,
            "tareas_pendientes": tareas_pendientes,
            "tareas_criticas": tareas_criticas,
            "workers_activos": workers_activos,
            "notificaciones_pendientes": notif_recientes,
            "vencidas_hoy": vencidas_hoy,
        }

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


class KanbanColumnPartialView(RoleRequiredMixin, TemplateView):
    template_name = "kanban/_column.html"
    roles_requeridos = ["administrador", "ti", "prevencion", "finanzas", "logistica"]

    def dispatch(self, request, *args, **kwargs):
        if request.headers.get("HX-Request") != "true" and not request.GET.get("partial"):
            return redirect("kanban:board")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        qs = _get_tasks_queryset(self.request)
        columna = self.kwargs.get("columna", "pendientes")

        estados_map = {
            "pendientes": [Task.EstadoChoices.PENDIENTE],
            "en-proceso": [Task.EstadoChoices.EN_PROCESO],
            "completadas": [
                Task.EstadoChoices.COMPLETADA,
                Task.EstadoChoices.GESTIONADO_EXTERNO,
            ],
        }
        estados = estados_map.get(columna, [Task.EstadoChoices.PENDIENTE])
        ctx["tasks"] = qs.filter(estado__in=estados)
        ctx["columna"] = columna
        ctx["user_roles"] = set(
            self.request.user.roles.values_list("nombre", flat=True)
        )
        return ctx


class KanbanCardDetailView(RoleRequiredMixin, TemplateView):
    template_name = "kanban/_card_detail.html"
    roles_requeridos = ["administrador", "ti", "prevencion", "finanzas", "logistica"]

    def get_template_names(self):
        if self.request.headers.get("HX-Request") == "true" or self.request.GET.get("partial"):
            return ["kanban/_card_detail.html"]
        return ["kanban/card_detail.html"]

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        task = get_object_or_404(
            Task.objects.select_related(
                "proceso__trabajador",
                "proceso__usuario_inicio",
                "proceso__ceco_origen",
                "proceso__ceco_destino",
                "usuario_responsable",
            ),
            pk=self.kwargs["pk"],
        )
        ctx["task"] = task
        ctx["user_roles"] = set(
            self.request.user.roles.values_list("nombre", flat=True)
        )
        ctx["es_responsable"] = task.usuario_responsable == self.request.user
        from apps.audit.models import AuditLog

        ctx["historial"] = AuditLog.objects.filter(
            tabla_afectada="tarea",
            id_entidad_afectada=task.pk,
        ).select_related("usuario")[:20]
        return ctx


class KanbanUpdateTaskView(RoleRequiredMixin, View):
    roles_requeridos = ["administrador", "ti", "prevencion", "finanzas", "logistica"]

    def post(self, request, pk):
        task = get_object_or_404(Task, pk=pk)
        nuevo_estado = request.POST.get("estado", "")

        if nuevo_estado not in dict(Task.EstadoChoices.choices):
            return JsonResponse({"error": "Estado no válido"}, status=400)

        responsable = task.usuario_responsable
        es_responsable = responsable == request.user
        es_admin = request.user.roles.filter(nombre="administrador").exists()

        if not (es_responsable or es_admin):
            return JsonResponse(
                {"error": "No tienes permiso para cambiar esta tarea"}, status=403
            )

        if nuevo_estado in (
            Task.EstadoChoices.COMPLETADA,
            Task.EstadoChoices.GESTIONADO_EXTERNO,
        ):
            anteriores = task.tareas_anteriores()
            if anteriores.exists():
                return JsonResponse(
                    {"error": "Complete primero las tareas previas"}, status=400
                )
            if (
                task.tipo == Task.TipoChoices.BLOQUEO_ACCESOS
                and task.proceso.tipo == Process.TipoChoices.TERMINO
            ):
                finiquito = task.proceso.tareas.filter(
                    tipo=Task.TipoChoices.FINIQUITO_COORDINACION
                ).first()
                if finiquito and finiquito.estado != Task.EstadoChoices.COMPLETADA:
                    return JsonResponse(
                        {"error": "Finanzas debe completar el finiquito primero"},
                        status=400,
                    )
            from apps.processes import services

            if nuevo_estado == Task.EstadoChoices.GESTIONADO_EXTERNO:
                services.gestionar_externamente_tarea(task)
            else:
                services.completar_tarea(task)
        else:
            task.estado = nuevo_estado
            task.save(update_fields=["estado"])

        return JsonResponse({"ok": True})


class KanbanLoadIndicatorView(RoleRequiredMixin, TemplateView):
    template_name = "kanban/_load_indicator.html"
    roles_requeridos = ["administrador", "ti", "prevencion", "finanzas", "logistica"]

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
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
