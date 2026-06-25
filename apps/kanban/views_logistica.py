from django.contrib import messages
from django.db import models as db_models
from django.shortcuts import redirect, get_object_or_404
from django.utils import timezone
from django.views.generic import TemplateView, ListView, View

from apps.accounts.decorators import RoleRequiredMixin
from apps.inventory.models import Asset, AssetAssignment, AssetType
from apps.processes.models import Process, Task


class LogisticaDashboardView(RoleRequiredMixin, TemplateView):
    template_name = "logistica/dashboard.html"
    roles_requeridos = ["administrador", "logistica"]

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        # Tareas de Logística
        mis_tareas = Task.objects.filter(
            tipo__in=[
                Task.TipoChoices.EQUIPAMIENTO,
                Task.TipoChoices.DEVOLUCION_ACTIVOS,
                Task.TipoChoices.RECUPERACION_ACTIVOS,
            ],
            omitida=False,
            proceso__estado=Process.EstadoChoices.EN_CURSO,
        ).select_related("proceso__trabajador", "usuario_responsable")

        tareas_pendientes = mis_tareas.filter(
            estado__in=[Task.EstadoChoices.PENDIENTE, Task.EstadoChoices.EN_PROCESO]
        )

        # Activos totales y asignados
        activos_totales = Asset.objects.count()
        activos_asignados = Asset.objects.filter(
            estado=Asset.EstadoChoices.ASIGNADO
        ).count()
        activos_disponibles = Asset.objects.filter(
            estado=Asset.EstadoChoices.DISPONIBLE
        ).count()
        activos_pendiente_devolucion = Asset.objects.filter(
            estado=Asset.EstadoChoices.PENDIENTE_DEVOLUCION
        ).count()

        # Devoluciones pendientes
        devoluciones_pendientes = AssetAssignment.objects.filter(
            fecha_devolucion__isnull=True,
            proceso__tipo__in=[
                Process.TipoChoices.TERMINO,
                Process.TipoChoices.DESPIDO,
            ],
            proceso__estado=Process.EstadoChoices.EN_CURSO,
        ).count()

        ctx["stats"] = {
            "tareas_pendientes": tareas_pendientes.count(),
            "activos_totales": activos_totales,
            "activos_asignados": activos_asignados,
            "activos_disponibles": activos_disponibles,
            "activos_pendiente_devolucion": activos_pendiente_devolucion,
            "devoluciones_pendientes": devoluciones_pendientes,
        }

        ctx["mis_tareas"] = tareas_pendientes.order_by("-urgencia", "plazo_limite")[:10]

        return ctx


class LogisticaDevolucionesView(RoleRequiredMixin, ListView):
    model = AssetAssignment
    template_name = "logistica/devoluciones.html"
    context_object_name = "asignaciones"
    roles_requeridos = ["administrador", "logistica"]
    paginate_by = 20

    def get_queryset(self):
        tipos_ti = AssetType.objects.filter(es_ti=True).values_list("pk", flat=True)
        qs = AssetAssignment.objects.filter(
            fecha_devolucion__isnull=False,
            activo__tipo__in=tipos_ti,
        ).select_related("activo__tipo", "trabajador", "proceso")

        q = self.request.GET.get("q", "").strip()
        estado_dev = self.request.GET.get("estado_devolucion", "")
        fecha_desde = self.request.GET.get("fecha_desde", "")
        fecha_hasta = self.request.GET.get("fecha_hasta", "")

        if q:
            qs = qs.filter(
                db_models.Q(activo__codigo__icontains=q)
                | db_models.Q(activo__nombre__icontains=q)
                | db_models.Q(trabajador__nombre__icontains=q)
            )
        if estado_dev:
            qs = qs.filter(estado_devolucion=estado_dev)
        if fecha_desde:
            qs = qs.filter(fecha_devolucion__date__gte=fecha_desde)
        if fecha_hasta:
            qs = qs.filter(fecha_devolucion__date__lte=fecha_hasta)

        return qs.order_by("-fecha_devolucion")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        tipos_ti = AssetType.objects.filter(es_ti=True)
        base = AssetAssignment.objects.filter(
            fecha_devolucion__isnull=False,
            activo__tipo__in=tipos_ti,
        )
        ctx["query"] = self.request.GET.get("q", "")
        ctx["filtro_estado"] = self.request.GET.get("estado_devolucion", "")
        ctx["fecha_desde"] = self.request.GET.get("fecha_desde", "")
        ctx["fecha_hasta"] = self.request.GET.get("fecha_hasta", "")
        ctx["total"] = base.count()
        return ctx


class LogisticaInventarioView(RoleRequiredMixin, ListView):
    model = Asset
    template_name = "logistica/inventario.html"
    context_object_name = "assets"
    roles_requeridos = ["administrador", "logistica"]
    paginate_by = 20

    def get_queryset(self):
        qs = Asset.objects.select_related("tipo")

        q = self.request.GET.get("q", "").strip()
        estado = self.request.GET.get("estado", "")
        tipo = self.request.GET.get("tipo", "")

        if q:
            qs = qs.filter(
                db_models.Q(codigo__icontains=q) | db_models.Q(nombre__icontains=q)
            )
        if estado:
            qs = qs.filter(estado=estado)
        if tipo:
            qs = qs.filter(tipo_id=tipo)

        if not self.request.GET.get("incluir_baja"):
            qs = qs.exclude(estado=Asset.EstadoChoices.DADO_DE_BAJA)

        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["query"] = self.request.GET.get("q", "")
        ctx["filtro_estado"] = self.request.GET.get("estado", "")
        ctx["filtro_tipo"] = self.request.GET.get("tipo", "")
        ctx["incluir_baja"] = self.request.GET.get("incluir_baja", "")
        ctx["tipos"] = AssetType.objects.filter(estado=AssetType.EstadoChoices.ACTIVO)
        return ctx


class LogisticaTableroView(RoleRequiredMixin, TemplateView):
    template_name = "logistica/tablero.html"
    roles_requeridos = ["administrador", "logistica"]

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        qs = Task.objects.filter(
            tipo__in=[
                Task.TipoChoices.EQUIPAMIENTO,
                Task.TipoChoices.DEVOLUCION_ACTIVOS,
                Task.TipoChoices.RECUPERACION_ACTIVOS,
            ],
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

        return ctx


class LogisticaRegistrarDevolucionView(RoleRequiredMixin, View):
    roles_requeridos = ["administrador", "logistica"]

    def post(self, request, pk):
        asignacion = get_object_or_404(AssetAssignment, pk=pk)

        estado_devolucion = request.POST.get("estado_devolucion")
        foto_evidencia_url = request.POST.get("foto_evidencia", "")
        foto_evidencia_file = request.FILES.get("foto_evidencia_file")

        if estado_devolucion not in dict(
            AssetAssignment.EstadoDevolucionChoices.choices
        ):
            messages.error(request, "Estado de devolución no válido.")
            return redirect("logistica:devoluciones")

        asignacion.fecha_devolucion = timezone.now()
        asignacion.estado_devolucion = estado_devolucion

        # Manejar subida de archivo (RF-22)
        if foto_evidencia_file:
            asignacion.foto_evidencia = foto_evidencia_file
            asignacion.foto_evidencia_url = ""  # Limpiar URL si hay archivo
        elif foto_evidencia_url:
            asignacion.foto_evidencia_url = foto_evidencia_url
            # No limpiar foto_evidencia para mantener archivo previo si existe

        asignacion.save()

        # Actualizar estado del activo según corresponda
        if asignacion.activo.estado == Asset.EstadoChoices.ASIGNADO:
            asignacion.activo.cambiar_estado(Asset.EstadoChoices.PENDIENTE_DEVOLUCION)

        if estado_devolucion == "bueno":
            asignacion.activo.cambiar_estado(Asset.EstadoChoices.DISPONIBLE)
        elif estado_devolucion == "danado":
            asignacion.activo.cambiar_estado(Asset.EstadoChoices.EN_REVISION)
        elif estado_devolucion == "con_perdida":
            asignacion.activo.motivo_baja = (
                f"Activo perdido durante devolución: {asignacion.activo.codigo}"
            )
            asignacion.activo.save(update_fields=["motivo_baja"])
            asignacion.activo.cambiar_estado(Asset.EstadoChoices.DADO_DE_BAJA)

        messages.success(
            request,
            f"Devolución de {asignacion.activo.nombre} registrada exitosamente.",
        )
        return redirect("logistica:devoluciones")

