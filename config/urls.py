from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', RedirectView.as_view(url='/kanban/', permanent=False), name='home'),
    path('', include('apps.accounts.urls')),
    path('', include('apps.clients.urls')),
    path('', include('apps.workers.urls')),
    path('', include('apps.inventory.urls')),
    path('', include('apps.processes.urls')),
    path('', include('apps.notifications.urls')),
    path('', include('apps.kanban.urls')),
]
