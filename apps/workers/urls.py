from django.urls import path
from . import views

app_name = 'workers'

urlpatterns = [
    path('trabajadores/', views.WorkerListView.as_view(), name='worker_list'),
    path('trabajadores/nuevo/', views.WorkerCreateView.as_view(), name='worker_create'),
    path('trabajadores/<int:pk>/', views.WorkerDetailView.as_view(), name='worker_detail'),
    path('trabajadores/<int:pk>/editar/', views.WorkerUpdateView.as_view(), name='worker_edit'),
    path('trabajadores/<int:pk>/eliminar/', views.WorkerDeleteView.as_view(), name='worker_delete'),
    path('trabajadores/<int:pk>/cambiar-estado/', views.WorkerStateChangeView.as_view(), name='worker_state_change'),
]
