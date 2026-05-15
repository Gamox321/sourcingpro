from django.urls import path
from . import views

app_name = 'kanban'

urlpatterns = [
    path('kanban/', views.KanbanBoardView.as_view(), name='board'),
    path('kanban/columna/<str:columna>/', views.KanbanColumnPartialView.as_view(), name='column_partial'),
    path('kanban/tarea/<int:pk>/', views.KanbanCardDetailView.as_view(), name='card_detail'),
    path('kanban/tarea/<int:pk>/actualizar/', views.KanbanUpdateTaskView.as_view(), name='update_task'),
    path('kanban/carga/', views.KanbanLoadIndicatorView.as_view(), name='load_indicator'),
]
