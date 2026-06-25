from django.urls import path
from . import views
from . import views_rrhh
from . import views_ti
from . import views_jefatura
from . import views_prevencion
from . import views_finanzas
from . import views_logistica

app_name = "kanban"

urlpatterns = [
    path("kanban/", views.KanbanBoardView.as_view(), name="board"),
    path(
        "kanban/columna/<str:columna>/",
        views.KanbanColumnPartialView.as_view(),
        name="column_partial",
    ),
    path(
        "kanban/tarea/<int:pk>/",
        views.KanbanCardDetailView.as_view(),
        name="card_detail",
    ),
    path(
        "kanban/tarea/<int:pk>/actualizar/",
        views.KanbanUpdateTaskView.as_view(),
        name="update_task",
    ),
    path(
        "kanban/carga/", views.KanbanLoadIndicatorView.as_view(), name="load_indicator"
    ),
]

rrhh_urlpatterns = (
    [
        path("", views_rrhh.RRHHDashboardView.as_view(), name="dashboard"),
        path(
            "trabajadores/",
            views_rrhh.RRHHTrabajadoresView.as_view(),
            name="trabajadores",
        ),
        path("procesos/", views_rrhh.RRHHProcesosView.as_view(), name="procesos"),
        path(
            "procesos/<int:pk>/",
            views_rrhh.RRHHProcesoDetailView.as_view(),
            name="proceso_detalle",
        ),
        path("cecos/", views_rrhh.RRHHCecosView.as_view(), name="cecos"),
        path("reportes/", views_rrhh.RRHHReportesView.as_view(), name="reportes"),
        path(
            "configuracion/plazos/",
            views_rrhh.RRHHConfigPlazosView.as_view(),
            name="config_plazos",
        ),
        path(
            "alertas/contratos/",
            views_rrhh.RRHHAlertasContratosView.as_view(),
            name="alertas_contratos",
        ),
        path(
            "procesos/<int:pk>/confirmar-cierre/",
            views_rrhh.RRHHConfirmarCierreTerminoView.as_view(),
            name="confirmar_cierre_termino",
        ),
    ],
    "rrhh",
)

ti_urlpatterns = (
    [
        path("", views_ti.TIDashboardView.as_view(), name="dashboard"),
        path("inventario/", views_ti.TIInventarioView.as_view(), name="inventario"),
        path(
            "inventario/nuevo/",
            views_ti.TIAssetCreateView.as_view(),
            name="asset_create",
        ),
        path("tablero/", views_ti.TITableroGeneralView.as_view(), name="tablero"),
        path(
            "bloqueo-urgente/",
            views_ti.TIBloqueoUrgenteView.as_view(),
            name="bloqueo_urgente",
        ),
        path(
            "bloqueo-urgente/<int:pk>/confirmar/",
            views_ti.TIConfirmarBloqueoView.as_view(),
            name="confirmar_bloqueo",
        ),
    ],
    "ti",
)

jefatura_urlpatterns = (
    [
        path("", views_jefatura.JefaturaNominaView.as_view(), name="nomina"),
        path(
            "trabajador/<int:pk>/",
            views_jefatura.JefaturaTrabajadorDetailView.as_view(),
            name="trabajador_detail",
        ),
        path("tablero/", views_jefatura.JefaturaTableroView.as_view(), name="tablero"),
        path(
            "procesos/", views_jefatura.JefaturaProcesosView.as_view(), name="procesos"
        ),
        path("ceco/", views_jefatura.JefaturaCeCoView.as_view(), name="ceco"),
        path(
            "ceco/<int:pk>/",
            views_jefatura.JefaturaCeCoView.as_view(),
            name="ceco_detail",
        ),
        path(
            "notificaciones/",
            views_jefatura.JefaturaNotificacionesView.as_view(),
            name="notificaciones",
        ),
    ],
    "jefatura",
)

prevencion_urlpatterns = (
    [
        path("", views_prevencion.PrevencionDashboardView.as_view(), name="dashboard"),
        path(
            "devoluciones/",
            views_prevencion.PrevencionDevolucionesView.as_view(),
            name="devoluciones",
        ),
        path(
            "inventario/",
            views_prevencion.PrevencionInventarioView.as_view(),
            name="inventario",
        ),
        path(
            "inventario/nuevo/",
            views_prevencion.PrevencionAssetCreateView.as_view(),
            name="asset_create",
        ),
        path(
            "certificaciones/",
            views_prevencion.PrevencionCertificacionesView.as_view(),
            name="certificaciones",
        ),
        path(
            "tablero/",
            views_prevencion.PrevencionTableroGeneralView.as_view(),
            name="tablero",
        ),
        path(
            "notificaciones/",
            views_prevencion.PrevencionNotificacionesView.as_view(),
            name="notificaciones",
        ),
    ],
    "prevencion",
)

finanzas_urlpatterns = (
    [
        path("", views_finanzas.FinanzasDashboardView.as_view(), name="dashboard"),
        path(
            "finiquitos/",
            views_finanzas.FinanzasFiniquitosView.as_view(),
            name="finiquitos",
        ),
        path("tablero/", views_finanzas.FinanzasTableroView.as_view(), name="tablero"),
        path(
            "notificaciones/",
            views_finanzas.FinanzasNotificacionesView.as_view(),
            name="notificaciones",
        ),
    ],
    "finanzas",
)

logistica_urlpatterns = (
    [
        path("", views_logistica.LogisticaDashboardView.as_view(), name="dashboard"),
        path(
            "devoluciones/",
            views_logistica.LogisticaDevolucionesView.as_view(),
            name="devoluciones",
        ),
        path(
            "devoluciones/<int:pk>/registrar/",
            views_logistica.LogisticaRegistrarDevolucionView.as_view(),
            name="registrar_devolucion",
        ),
        path(
            "inventario/",
            views_logistica.LogisticaInventarioView.as_view(),
            name="inventario",
        ),
        path(
            "tablero/", views_logistica.LogisticaTableroView.as_view(), name="tablero"
        ),
    ],
    "logistica",
)
