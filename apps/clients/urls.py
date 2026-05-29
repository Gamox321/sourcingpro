from django.urls import path
from . import views

app_name = 'clients'

urlpatterns = [
    path('centros-costo/', views.CostCenterListView.as_view(), name='costcenter_list'),
    path('centros-costo/nuevo/', views.CostCenterCreateView.as_view(), name='costcenter_create'),
    path('centros-costo/<int:pk>/', views.CostCenterDetailView.as_view(), name='costcenter_detail'),
    path('centros-costo/<int:pk>/editar/', views.CostCenterUpdateView.as_view(), name='costcenter_edit'),
    path('centros-costo/<int:pk>/toggle-estado/', views.CostCenterDeactivateView.as_view(), name='costcenter_toggle'),
]
