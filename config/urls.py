from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView

from apps.kanban.urls import rrhh_urlpatterns, ti_urlpatterns, jefatura_urlpatterns, prevencion_urlpatterns, finanzas_urlpatterns, logistica_urlpatterns


class SmartRedirectView(RedirectView):
    permanent = False

    def get_redirect_url(self, *args, **kwargs):
        if self.request.user.is_authenticated:
            user_roles = set(
                self.request.user.roles.values_list('nombre', flat=True)
            )
            if 'rrhh' in user_roles and 'administrador' not in user_roles:
                return '/rrhh/'
            elif 'ti' in user_roles and 'administrador' not in user_roles and 'rrhh' not in user_roles:
                return '/ti/'
            elif 'jefatura' in user_roles and 'administrador' not in user_roles and 'rrhh' not in user_roles and 'ti' not in user_roles:
                return '/jefatura/'
            elif 'prevencion' in user_roles and 'administrador' not in user_roles and 'rrhh' not in user_roles and 'ti' not in user_roles and 'jefatura' not in user_roles:
                return '/prevencion/'
            elif 'finanzas' in user_roles and 'administrador' not in user_roles and 'rrhh' not in user_roles and 'ti' not in user_roles and 'prevencion' not in user_roles and 'jefatura' not in user_roles:
                return '/finanzas/'
            elif 'logistica' in user_roles and 'administrador' not in user_roles and 'rrhh' not in user_roles and 'ti' not in user_roles and 'prevencion' not in user_roles and 'jefatura' not in user_roles and 'finanzas' not in user_roles:
                return '/logistica/'
        return '/kanban/'


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', SmartRedirectView.as_view(), name='home'),
    path('rrhh/', include(rrhh_urlpatterns)),
    path('ti/', include(ti_urlpatterns)),
    path('jefatura/', include(jefatura_urlpatterns)),
    path('prevencion/', include(prevencion_urlpatterns)),
    path('finanzas/', include(finanzas_urlpatterns)),
    path('logistica/', include(logistica_urlpatterns)),
    path('', include('apps.accounts.urls')),
    path('', include('apps.clients.urls')),
    path('', include('apps.workers.urls')),
    path('', include('apps.inventory.urls')),
    path('', include('apps.processes.urls')),
    path('', include('apps.notifications.urls')),
    path('', include('apps.kanban.urls')),
]
