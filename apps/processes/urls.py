from django.urls import path
from . import views

app_name = 'processes'

urlpatterns = [
    path('procesos/', views.ProcessListView.as_view(), name='process_list'),
    path('procesos/nuevo/', views.ProcessTypeSelectView.as_view(), name='process_type_select'),
    path('procesos/nuevo/contratacion/', views.ProcessCreateContratacionView.as_view(), name='process_create_contratacion'),
    path('procesos/nuevo/cambio-ceco/', views.ProcessCreateCambioCeCoView.as_view(), name='process_create_cambio_ceco'),
    path('procesos/nuevo/termino/', views.ProcessCreateTerminoView.as_view(), name='process_create_termino'),
    path('procesos/nuevo/despido/', views.ProcessCreateDespidoView.as_view(), name='process_create_despido'),
    path('procesos/<int:pk>/', views.ProcessDetailView.as_view(), name='process_detail'),
    path('procesos/<int:pk>/cerrar/', views.ProcessCloseView.as_view(), name='process_close'),
    path('procesos/<int:pk>/tareas/<int:task_pk>/completar/', views.TaskCompleteView.as_view(), name='task_complete'),
    path('procesos/<int:pk>/tareas/<int:task_pk>/editar/', views.TaskUpdateView.as_view(), name='task_update'),
]
