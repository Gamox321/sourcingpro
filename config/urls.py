from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView

from apps.accounts.utils import get_primary_role
from apps.kanban.urls import (
    rrhh_urlpatterns,
    ti_urlpatterns,
    jefatura_urlpatterns,
    prevencion_urlpatterns,
    finanzas_urlpatterns,
    logistica_urlpatterns,
)


class SmartRedirectView(RedirectView):
    permanent = False

    def get_redirect_url(self, *args, **kwargs):
        if self.request.user.is_authenticated:
            user_roles = set(self.request.user.roles.values_list("nombre", flat=True))
            primary = get_primary_role(user_roles)
            if (
                primary
                and primary != "administrador"
                and "administrador" not in user_roles
            ):
                return f"/{primary}/"
        return "/kanban/"


urlpatterns = [
    path("admin/", admin.site.urls),
    path("", SmartRedirectView.as_view(), name="home"),
    path("rrhh/", include(rrhh_urlpatterns)),
    path("ti/", include(ti_urlpatterns)),
    path("jefatura/", include(jefatura_urlpatterns)),
    path("prevencion/", include(prevencion_urlpatterns)),
    path("finanzas/", include(finanzas_urlpatterns)),
    path("logistica/", include(logistica_urlpatterns)),
    path("", include("apps.accounts.urls")),
    path("", include("apps.clients.urls")),
    path("", include("apps.workers.urls")),
    path("", include("apps.inventory.urls")),
    path("", include("apps.processes.urls")),
    path("", include("apps.notifications.urls")),
    path("", include("apps.kanban.urls")),
]
