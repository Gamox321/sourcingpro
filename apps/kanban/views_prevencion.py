from datetime import timedelta

from django.contrib import messages
from django.db import models as db_models
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import TemplateView, ListView, CreateView

from apps.accounts.decorators import RoleRequiredMixin
from apps.inventory.models import Asset, AssetType
from apps.notifications.views import NotificationListView
from apps.processes.models import Process, Task


PREVENCION_TASK_TYPES = [
    Task.TipoChoices.EXAMENES_PREOCUPACIONALES,
    Task.TipoChoices.EPP_INDUCCION,
]


class PrevencionDashboardView(RoleRequiredMixin, TemplateView):
    template_name = "prevencion/dashboard.html"
    roles_requeridos = ["administrador", "prevencion"]

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        now = timezone.now()

        mis_tareas = Task.objects.filter(
            usuario_responsable=self.request.user,
            tipo__in=PREVENCION_TASK_TYPES,
            omitida=False,
            proceso__estado=Process.EstadoChoices.EN_CURSO,
        ).select_related(
            "proceso__trabajador", "proceso__ceco_origen", "proceso__ceco_destino"
        )

        tareas_activas = mis_tareas.filter(
            estado__in=[Task.EstadoChoices.PENDIENTE, Task.EstadoChoices.EN_PROCESO]
        )

        tipos_epp = AssetType.objects.filter(
            es_prevencion=True, estado="activo"
        ).values_list("pk", flat=True)
        if tipos_epp:
            epp_total = Asset.objects.filter(tipo__in=tipos_epp)
            epp_asignados = epp_total.filter(
                estado=Asset.EstadoChoices.ASIGNADO
            ).count()
            epp_disponibles = epp_total.filter(
                estado=Asset.EstadoChoices.DISPONIBLE
            ).count()
            inventario_epp = (
                Asset.objects.filter(tipo__in=tipos_epp)
                .select_related("tipo")
                .prefetch_related("asignaciones__trabajador")[:5]
            )
        else:
            epp_asignados = 0
            epp_disponibles = 0
            inventario_epp = Asset.objects.none()

        examenes_pendientes = mis_tareas.filter(
            tipo=Task.TipoChoices.EXAMENES_PREOCUPACIONALES,
            estado__in=[Task.EstadoChoices.PENDIENTE, Task.EstadoChoices.EN_PROCESO],
            plazo_limite__lte=now + timedelta(days=7),
        ).count()

        ctx["stats"] = {
            "tareas_activas": tareas_activas.count(),
            "epp_asignados": epp_asignados,
            "epp_disponibles": epp_disponibles,
            "examenes_pendientes": examenes_pendientes,
        }

        ctx["mis_tareas"] = tareas_activas.order_by("-urgencia", "plazo_limite")[:10]
        ctx["total_mis_tareas"] = tareas_activas.count()
        ctx["inventario_epp"] = inventario_epp

        prox_30_dias = now + timedelta(days=30)
        tareas_cert = (
            Task.objects.filter(
                tipo=Task.TipoChoices.EXAMENES_PREOCUPACIONALES,
                omitida=False,
                proceso__estado=Process.EstadoChoices.EN_CURSO,
                estado__in=[
                    Task.EstadoChoices.PENDIENTE,
                    Task.EstadoChoices.EN_PROCESO,
                ],
                plazo_limite__lte=prox_30_dias,
            )
            .select_related("proceso__trabajador")
            .order_by("plazo_limite")[:3]
        )

        certificaciones = []
        for tarea in tareas_cert:
            dias = (tarea.plazo_limite - now).days if tarea.plazo_limite else 0
            if dias <= 7:
                urgencia, color, pct = "critica", "#E24B4A", 90
            elif dias <= 14:
                urgencia, color, pct = "alta", "#EF9F27", 60
            else:
                urgencia, color, pct = "normal", "#639922", 30
            certificaciones.append(
                {
                    "tarea": tarea,
                    "dias_restantes": dias,
                    "urgencia": urgencia,
                    "color": color,
                    "pct": pct,
                }
            )

        ctx["certificaciones"] = certificaciones
        ctx["total_certificaciones_prox"] = tareas_cert.count()

        return ctx


class PrevencionInventarioView(RoleRequiredMixin, ListView):
    model = Asset
    template_name = "prevencion/inventario.html"
    context_object_name = "assets"
    roles_requeridos = ["administrador", "prevencion"]
    paginate_by = 20

    def get_queryset(self):
        tipos_epp = AssetType.objects.filter(
            es_prevencion=True, estado="activo"
        ).values_list("pk", flat=True)
        if not tipos_epp:
            return Asset.objects.none()
        qs = Asset.objects.filter(tipo__in=tipos_epp).select_related("tipo")

        q = self.request.GET.get("q", "").strip()
        estado = self.request.GET.get("estado", "")

        if q:
            qs = qs.filter(
                db_models.Q(codigo__icontains=q) | db_models.Q(nombre__icontains=q)
            )
        if estado:
            qs = qs.filter(estado=estado)

        if not self.request.GET.get("incluir_baja"):
            qs = qs.exclude(estado=Asset.EstadoChoices.DADO_DE_BAJA)

        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["query"] = self.request.GET.get("q", "")
        ctx["filtro_estado"] = self.request.GET.get("estado", "")
        ctx["incluir_baja"] = self.request.GET.get("incluir_baja", "")
        return ctx


class PrevencionCertificacionesView(RoleRequiredMixin, TemplateView):
    template_name = "prevencion/certificaciones.html"
    roles_requeridos = ["administrador", "prevencion"]

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        now = timezone.now()
        prox_30_dias = now + timedelta(days=30)

        tareas_certificaciones = (
            Task.objects.filter(
                tipo=Task.TipoChoices.EXAMENES_PREOCUPACIONALES,
                omitida=False,
                proceso__estado=Process.EstadoChoices.EN_CURSO,
                estado__in=[
                    Task.EstadoChoices.PENDIENTE,
                    Task.EstadoChoices.EN_PROCESO,
                ],
                plazo_limite__lte=prox_30_dias,
            )
            .select_related("proceso__trabajador")
            .order_by("plazo_limite")
        )

        certificaciones = []
        for tarea in tareas_certificaciones:
            dias_restantes = (
                (tarea.plazo_limite - now).days if tarea.plazo_limite else 0
            )

            if dias_restantes <= 7:
                urgencia = "critica"
            elif dias_restantes <= 14:
                urgencia = "alta"
            else:
                urgencia = "normal"

            certificaciones.append(
                {
                    "tarea": tarea,
                    "dias_restantes": dias_restantes,
                    "urgencia": urgencia,
                }
            )

        ctx["certificaciones"] = certificaciones
        ctx["total_certificaciones"] = len(certificaciones)

        return ctx


class PrevencionTableroGeneralView(RoleRequiredMixin, TemplateView):
    template_name = "prevencion/tablero.html"
    roles_requeridos = ["administrador", "prevencion"]

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        qs = Task.objects.filter(
            tipo__in=PREVENCION_TASK_TYPES,
            omitida=False,
            proceso__estado=Process.EstadoChoices.EN_CURSO,
        ).select_related(
            "proceso__trabajador", "usuario_responsable", "proceso__ceco_origen"
        )

        tipo_proceso = self.request.GET.get("tipo_proceso", "")
        ctx["filtro_tipo_proceso"] = tipo_proceso
        if tipo_proceso:
            qs = qs.filter(proceso__tipo=tipo_proceso)

        ctx["pendientes"] = qs.filter(estado=Task.EstadoChoices.PENDIENTE)
        ctx["en_proceso"] = qs.filter(estado=Task.EstadoChoices.EN_PROCESO)
        ctx["completadas"] = qs.filter(
            estado__in=[
                Task.EstadoChoices.COMPLETADA,
                Task.EstadoChoices.GESTIONADO_EXTERNO,
            ]
        )

        return ctx


class PrevencionAssetCreateView(RoleRequiredMixin, CreateView):
    model = Asset
    template_name = "prevencion/asset_form.html"
    fields = ["codigo", "nombre", "tipo"]
    roles_requeridos = ["administrador", "prevencion"]
    success_url = reverse_lazy("prevencion:inventario")

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields["tipo"].queryset = AssetType.objects.filter(
            es_prevencion=True, estado=AssetType.EstadoChoices.ACTIVO
        )
        form.fields["tipo"].empty_label = "— Seleccionar tipo —"
        return form

    def form_valid(self, form):
        form.instance.estado = Asset.EstadoChoices.DISPONIBLE
        tipo_nombre = form.instance.tipo.nombre
        messages.success(
            self.request, f'{tipo_nombre} "{form.instance.nombre}" creado exitosamente.'
        )
        return super().form_valid(form)


class PrevencionNotificacionesView(NotificationListView):
    template_name = "prevencion/notificaciones.html"
    roles_requeridos = ["administrador", "prevencion"]
