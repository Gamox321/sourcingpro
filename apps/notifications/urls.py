from django.urls import path
from . import views

app_name = 'notifications'

urlpatterns = [
    path('notificaciones/', views.NotificationListView.as_view(), name='list'),
    path('notificaciones/contar/', views.NotificationCountView.as_view(), name='count'),
    path('notificaciones/dropdown/', views.NotificationDropdownView.as_view(), name='dropdown'),
    path('notificaciones/<int:pk>/leer/', views.NotificationMarkReadView.as_view(), name='mark_read'),
    path('notificaciones/leer-todas/', views.NotificationMarkAllReadView.as_view(), name='mark_all_read'),
    path('notificaciones/<int:pk>/eliminar/', views.NotificationDeleteView.as_view(), name='delete'),
]
